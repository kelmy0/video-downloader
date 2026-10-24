"""
config/manager.py

Module responsible for managing the loading of global configurations and
registered channels, cooldown validation, and state persistence.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple
from schemas.config_schema import AppConfig
from schemas.channel_schema import BaseChannelConfig


class ConfigManager:
    """Centralized manager for channel settings and status."""

    def __init__(self):
        self.base_directory: Path = Path.cwd()
        self.config_dir: Path = self.base_directory / "config"
        self.config_path: Path = self.config_dir / "config.json"
        self.channels_path: Path = self.config_dir / "channels.json"

    def load_configs(self) -> Tuple[Optional[Path], int, Optional[Path]]:
        """
        Validates and loads config.json.
        """
        print(f"\033[34m[INFO]\033[0m System base directory: {self.base_directory}")

        if not self.config_path.exists():
            print(f"\033[31m[CRITICAL ERROR]\033[0m Configuration file not found in: {self.config_path}")
            return None, 0, None

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                app_config: AppConfig = json.load(f)

            raw_download_path: str = ""
            raw_cookies_path: str = ""

            if "path" in app_config:
                path_config = app_config["path"]
                raw_download_path = path_config.get("download_path", "")
                raw_cookies_path = path_config.get("cookies_path", "")

            cooldown_minutes: int = app_config.get("cooldown_minutes", 0)

            if not raw_download_path:
                print(
                    f"\033[31m[CRITICAL ERROR]\033[0m The 'path.download_path' parameter has not been defined in config.json."
                )
                return None, 0, None

            root_download_dir = Path(raw_download_path)

            cookies_path: Optional[Path] = None
            if raw_cookies_path:
                potential_path = Path(raw_cookies_path)

                if potential_path.is_dir() or not potential_path.name.endswith(".txt"):
                    potential_path = potential_path / "cookies.txt"

                if potential_path.exists():
                    cookies_path = potential_path
                    print(f"\033[34m[INFO]\033[0m Cookie file loaded successfully: {cookies_path}")
                else:
                    print(
                        f"\033[33m[WARNING]\033[0m The provided cookie path was not found or is invalid: {potential_path}"
                    )
                    print(f"\033[33m[WARNING]\033[0m The system will continue execution without cookie authentication.")
            else:
                print(f"\033[34m[INFO]\033[0m No cookie path configured. Running in public mode.")

        except Exception as e:
            print(f"\033[31m[CRITICAL ERROR]\033[0m Failed to read config.json: {e}")
            return None, 0, None

        print(f"\033[34m[INFO]\033[0m Root downloads directory: {root_download_dir.resolve()}")

        return root_download_dir, cooldown_minutes, cookies_path

    def load_channels(self) -> List[BaseChannelConfig]:
        """
        Loads the generic list of channels that extend BaseChannelConfig.
        """
        if not self.channels_path.exists():
            print(f"\033[31m[CRITICAL ERROR]\033[0m The channels.json file was not found in: {self.channels_path}")
            return []

        try:
            with open(self.channels_path, "r", encoding="utf-8") as f:
                channels_data = json.load(f)
        except Exception as e:
            print(f"\033[31m[CRITICAL ERROR]\033[0m Failed to read the channels.json file: {e}")
            return []

        channels: List[BaseChannelConfig] = channels_data.get("channels", [])
        if not channels:
            print("\033[34m[INFO]\033[0m No channels configured in the channels.json file.")
            return []

        return channels

    def check_cooldown(self, channel_config: BaseChannelConfig, cooldown_minutes: int, now: datetime) -> bool:
        """
        Checks whether the channel is in a cooldown period. Returns True if the channel should be SKIPPED.
        """
        last_checked_str: Optional[str] = channel_config.get("last_checked")
        name: str = channel_config.get("name", "Channel")

        if cooldown_minutes <= 0:
            print("\033[33m[WARNING]\033[0m Cooldown is disabled; all channels will be analyzed.")

        if cooldown_minutes > 0 and last_checked_str:
            try:
                last_analysis = datetime.strptime(last_checked_str, "%Y-%m-%d %H:%M:%S")
                delta_time = now - last_analysis
                cooldown_limit = timedelta(minutes=cooldown_minutes)

                if delta_time < cooldown_limit:
                    time_remaining = cooldown_limit - delta_time
                    minutes_remaining = int(time_remaining.total_seconds() // 60)
                    seconds_remaining = int(time_remaining.total_seconds() % 60)
                    print(
                        f"\033[34m[COOLDOWN]\033[0m Channel '{name}' ignored. On cooldown ({minutes_remaining}m {seconds_remaining}s remaining)."
                    )
                    return True
            except ValueError:
                pass

        return False

    def save_channel_changes(self, channels: List[BaseChannelConfig]) -> None:
        """
        Saves the updated state back to channels.json.
        """

        try:
            channels_data = {"channels": channels}
            with open(self.channels_path, "w", encoding="utf-8") as f:
                json.dump(channels_data, f, indent=4, ensure_ascii=False)
                print(f"\n\033[34m[MEMORY]\033[0m 'last_checked' state successfully updated in channels.json.")

        except Exception as e:
            print(f"\n\033[33m[WARNING]\033[0m Failed to update the channels.json file: {e}")
