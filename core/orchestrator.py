"""
core/orchestrator.py

Module responsible for managing the execution flow of channel archiving routines.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from config.manager import ConfigManager
from core.base import PlatformExtractor
from core.channel_processor import ChannelProcessor
from core.dependencies import DependencyChecker
from schemas.channel_schema import BaseChannelConfig
from schedulers.factory import SchedulerFactory


class ChannelArchiverOrchestrator:
    """Orchestrator of the archiving lifecycle for channels."""

    def __init__(self, config_manager: ConfigManager, extractors: Dict[str, PlatformExtractor[Any]]) -> None:
        self.config_manager = config_manager
        self.extractors = extractors
        self.processor = ChannelProcessor(config_manager, extractors)

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

    def run(self) -> None:
        """Validates environment, sets up schedules, and executes the channel archiving loop."""
        # 1. Check the project dependencies
        if not DependencyChecker.validate_enviroment():
            return

        # 2. Load global configurations
        root_download_dir, cooldown_minutes, cookies_path, scheduler_config = self.config_manager.load_configs()
        if not root_download_dir or not scheduler_config:
            return

        # 3. Load channels configuration
        channels: List[BaseChannelConfig] = self.config_manager.load_channels()
        if not channels:
            return

        # 4. Setup scheduler if configured
        if "interval_minutes" in scheduler_config and "enable_on_startup" in scheduler_config:
            scheduler = SchedulerFactory.get_scheduler()
            if not scheduler.setup_schedule(
                scheduler_config["interval_minutes"], scheduler_config["enable_on_startup"]
            ):
                print("\033[33m[WARNING]\033[0m Some task schedules failed.")

        now: datetime = datetime.now()
        there_is_change_in_channels: bool = False

        # 5. Process each registered channel
        for idx, channel_config in enumerate(channels, start=1):
            name = channel_config.get("name", f"Channel_{idx}")
            platform_name = channel_config.get("platform", "").lower()

            print(f"\n\033[36m--------------------------------------------------\033[0m")
            print(f"\033[1m[{idx}/{len(channels)}] Processing: {name} (Platform: {platform_name})\033[0m")
            print(f"\033[36m--------------------------------------------------\033[0m")

            # Execute channel processing via dedicated processor module
            processed_successfully = self.processor.process_channel(
                channel_config=channel_config,
                root_download_dir=root_download_dir,
                cooldown_minutes=cooldown_minutes,
                cookies_path=cookies_path,
                now=now,
            )

            if processed_successfully:
                there_is_change_in_channels = True

        # 6. Save state changes if any occurred
        if there_is_change_in_channels:
            self.config_manager.save_channel_changes(channels)

        # 7. Retry download suboptimal media items
        self.processor.process_retry_queue(root_download_dir=root_download_dir, cookies_path=cookies_path)
