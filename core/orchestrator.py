"""
core/orchestrator.py

Module responsible for managing the execution of channel scanning,
cooldown validation, calls to extractors, and the execution of downloads.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from core.base import PlatformExtractor
from core.downloader import MediaDownloader
from core.dependencies import DependencyChecker
from config.manager import ConfigManager
from schemas.channel_schema import BaseChannelConfig
from schedulers.factory import SchedulerFactory


class ChannelArchiverOrchestrator:
    """Orchestrator of the archiving lifecycle for channels."""

    def __init__(self, config_manager: ConfigManager, extractors: Dict[str, PlatformExtractor[Any]]) -> None:
        self.config_manager = config_manager
        self.extractors = extractors

    def _load_archived_ids(self, archive_path: Path) -> Set[Tuple[str, str]]:
        """
        Reads the yt-dlp `archive.txt` file and returns a set containing only the IDs
        of the videos already downloaded.
        """
        downloaded_ids: Set[Tuple[str, str]] = set()
        if not archive_path.exists():
            return downloaded_ids

        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        platform = parts[0].lower()
                        video_id = parts[1]
                        downloaded_ids.add((platform, video_id))
        except Exception as e:
            print(f"\033[33m[WARNING]\033[0m Failed to read the file archive.txt: {e}")

        return downloaded_ids

    def executar(self) -> None:
        # Check the project dependencies
        if not DependencyChecker.validate_enviroment():
            return

        root_download_dir, cooldown_minutes, cookies_path, scheduler_config = self.config_manager.load_configs()
        if not root_download_dir or not scheduler_config:
            return

        channels: List[BaseChannelConfig] = self.config_manager.load_channels()
        if not channels:
            return

        if "interval_minutes" in scheduler_config and "enable_on_startup" in scheduler_config:
            scheduler = SchedulerFactory.get_scheduler()
            if not scheduler.setup_schedule(
                scheduler_config["interval_minutes"], scheduler_config["enable_on_startup"]
            ):
                print(f"\033[33m[WARNING]\033[0m Some task schedules failed.")

        now: datetime = datetime.now()
        there_is_change_in_channels: bool = False

        for idx, channel_config in enumerate(channels, start=1):
            name = channel_config.get("name", f"Canal_{idx}")
            platform_name = channel_config.get("platform", "").lower()
            feed_url = channel_config.get("feed_url")
            folder_name = channel_config.get("folder_name")

            print(f"\n\033[36m--------------------------------------------------\033[0m")
            print(f"\033[1m[{idx}/{len(channels)}] Processing: {name} (Platform: {platform_name})\033[0m")
            print(f"\033[36m--------------------------------------------------\033[0m")

            # Cooldown
            if self.config_manager.check_cooldown(channel_config, cooldown_minutes, now):
                continue

            if not platform_name or not feed_url or not folder_name:
                print(f"\033[33m[WARNING]\033[0m Incomplete configuration for channel '{name}'. Skipping.")
                continue

            extractor = self.extractors.get(platform_name)
            if not extractor:
                print(f"\033[33m[WARNING]\033[0m Platform '{platform_name}' is not supported or not registered.")
                continue

            output_dir = root_download_dir / folder_name
            archive_path = output_dir / "archive.txt"

            print(f"\033[34m[INFO]\033[0m Destination folder: {output_dir.resolve()}")

            # 1. Loads the (platform, id) pairs already downloaded from the disk
            pairs_already_downloaded = self._load_archived_ids(archive_path)

            # 2. Extracts platform-specific options
            options = extractor.extract_options(channel_config)

            # 3. Gets all items from the feed
            items = extractor.fetch_new_items(feed_url, options=options)

            channel_config["last_checked"] = now.strftime("%Y-%m-%d %H:%M:%S")
            there_is_change_in_channels = True

            if not items:
                print(f"\033[34m[INFO]\033[0m No items were returned by the feed for '{name}'.")
                continue

            # 4. MULTI-PLATFORM OPTIMIZATION: Validates by combining the current platform and the item ID
            platform_name = extractor.name.lower()
            new_items = [item for item in items if (platform_name, item.id) not in pairs_already_downloaded]
            total_skipped = len(items) - len(new_items)

            print(
                f"\033[34m[INFO]\033[0m Total in the feed: {len(items)} | Already downloaded: {total_skipped} |\033[32m New items to download: {len(new_items)}\033[0m"
            )

            if not new_items:
                print(f"\033[32m[INFO]\033[0m No new videos to process on this channel.")
                continue

            for item in new_items:
                print(f"\n\033[33m[PROCESSING ITEM]\033[0m {item.title} (ID: {item.id})")

                command = extractor.get_download_command(
                    item_url=item.url, output_dir=output_dir, archive_path=archive_path, cookies_path=cookies_path
                )
                success = MediaDownloader.execute(command, output_dir)

                if not success:
                    print(f"\033[31m[ERROR]\033[0m The download of item {item.id} failed or was skipped.")

        if there_is_change_in_channels:
            self.config_manager.save_channel_changes(channels)
