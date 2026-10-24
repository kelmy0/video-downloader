"""
core/channel_processor.py

Module responsible for handling individual channel validation, cooldown checks,
feed extraction, archive matching, and media downloads.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Set, Tuple, Optional

from config.manager import ConfigManager
from core.base import PlatformExtractor
from core.downloader import MediaDownloader
from schemas.channel_schema import BaseChannelConfig


class ChannelProcessor:
    """Handles the processing pipeline for a single channel configuration."""

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

    def process_channel(
        self,
        channel_config: BaseChannelConfig,
        root_download_dir: Path,
        cooldown_minutes: int,
        cookies_path: Optional[Path],
        now: datetime,
    ) -> bool:
        """
        Processes a single channel: checks cooldown, fetches new items, matches archive history,
        and downloads missing media items. Returns True if the channel state was updated.
        """
        name = channel_config.get("name", "Unknown_Channel")
        platform_name = channel_config.get("platform", "").lower()
        feed_url = channel_config.get("feed_url")
        folder_name = channel_config.get("folder_name")

        # 1. Cooldown validation
        if self.config_manager.check_cooldown(channel_config, cooldown_minutes, now):
            return False

        # 2. Configuration completeness validation
        if not platform_name or not feed_url or not folder_name:
            print(f"\033[33m[WARNING]\033[0m Incomplete configuration for channel '{name}'. Skipping.")
            return False

        # 3. Extractor resolution
        extractor = self.extractors.get(platform_name)
        if not extractor:
            print(f"\033[33m[WARNING]\033[0m Platform '{platform_name}' is not supported or not registered.")
            return False

        output_dir = root_download_dir / folder_name
        archive_path = output_dir / "archive.txt"

        print(f"\033[34m[INFO]\033[0m Destination folder: {output_dir.resolve()}")

        # 4. Load already archived IDs from disk
        pairs_already_downloaded = self._load_archived_ids(archive_path)

        # 5. Extract platform-specific options and fetch feed items
        options = extractor.extract_options(channel_config)
        items = extractor.fetch_new_items(feed_url, options=options)

        # Update last checked timestamp
        channel_config["last_checked"] = now.strftime("%Y-%m-%d %H:%M:%S")

        if not items:
            print(f"\033[34m[INFO]\033[0m No items were returned by the feed for '{name}'.")
            return True

        # 6. Filter out already downloaded items
        norm_platform_name = extractor.name.lower()
        new_items = [item for item in items if (norm_platform_name, item.id) not in pairs_already_downloaded]
        total_skipped = len(items) - len(new_items)

        print(
            f"\033[34m[INFO]\033[0m Total in the feed: {len(items)} | Already downloaded: {total_skipped} | "
            f"\033[32mNew items to download: {len(new_items)}\033[0m"
        )

        if not new_items:
            print(f"\033[32m[INFO]\033[0m No new videos to process on this channel.")
            return True

        # 7. Execute downloads for new items
        for item in new_items:
            print(f"\n\033[33m[PROCESSING ITEM]\033[0m {item.title} (ID: {item.id})")

            command = extractor.get_download_command(
                item_url=item.url, output_dir=output_dir, archive_path=archive_path, cookies_path=cookies_path
            )
            success = MediaDownloader.execute(command, output_dir)

            if not success:
                print(f"\033[31m[ERROR]\033[0m The download of item {item.id} failed or was skipped.")

        return True
