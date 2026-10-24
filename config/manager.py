"""
config/manager.py

Module responsible for managing the loading of global configurations and
registered channels, cooldown validation, and state persistence.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple, Any, Dict, cast
from schemas.config_schema import SchedulerConfig, AppConfig
from schemas.channel_schema import BaseChannelConfig


class ConfigManager:
    """Centralized manager for channel settings and status."""

    def __init__(self):
        self.base_directory: Path = Path.cwd()
        self.config_dir: Path = self.base_directory / "config"
        self.config_path: Path = self.config_dir / "config.json"
        self.channels_path: Path = self.config_dir / "channels.json"

    def _read_json_file(self, file_path: Path) -> Optional[Any]:
        """Safely reads and parses a JSON file."""
        if not file_path.exists():
            print(f"\033[31m[CRITICAL ERROR]\033[0m File not found in: {file_path}")
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"\033[31m[CRITICAL ERROR]\033[0m Failed to parse JSON file {file_path.name}: {e}")
            return None

    def _validate_path_config(self, path_data: Dict[str, Any]) -> Optional[Tuple[Path, Optional[Path]]]:
        """Strictly validates and extracts download path and optional cookies path."""
        raw_download_path = path_data.get("download_path")
        if not isinstance(raw_download_path, str) or not raw_download_path.strip():
            print(
                "\033[31m[CRITICAL ERROR]\033[0m The 'path.download_path' parameter is mandatory and must be a non-empty string."
            )
            return None

        root_download_dir = Path(raw_download_path)

        raw_cookies_path = path_data.get("cookies_path")
        cookies_path: Optional[Path] = None

        if raw_cookies_path is not None:
            if not isinstance(raw_cookies_path, str):
                print("\033[31m[CRITICAL ERROR]\033[0m The 'path.cookies_path' parameter must be a string if provided.")
                return None

            if raw_cookies_path.strip():
                potential_path = Path(raw_cookies_path)
                if potential_path.is_dir() or not potential_path.name.endswith(".txt"):
                    potential_path = potential_path / "cookies.txt"

                if potential_path.exists():
                    cookies_path = potential_path
                    print(f"\033[34m[INFO]\033[0m Cookie file loaded successfully: {cookies_path}")
                else:
                    print(f"\033[33m[WARNING]\033[0m Provided cookie path not found or invalid: {potential_path}")
                    print(f"\033[33m[WARNING]\033[0m System will continue execution without cookie authentication.")
            else:
                print(f"\033[34m[INFO]\033[0m Empty cookie path configured. Running in public mode.")
        else:
            print(f"\033[34m[INFO]\033[0m No cookie path configured. Running in public mode.")

        return root_download_dir, cookies_path

    def _validate_cooldown(self, cooldown_data: Any) -> Optional[int]:
        """Strictly validates cooldown_minutes (must be an integer, excluding booleans)."""
        if cooldown_data is None:
            print("\033[31m[CRITICAL ERROR]\033[0m The 'cooldown_minutes' field is mandatory.")
            return None

        if not isinstance(cooldown_data, int) or isinstance(cooldown_data, bool):
            print(
                f"\033[31m[CRITICAL ERROR]\033[0m The 'cooldown_minutes' parameter must be an integer "
                f"(received: {type(cooldown_data).__name__})."
            )
            return None

        return cooldown_data

    def _validate_scheduler_config(self, scheduler_data: Any) -> Optional[SchedulerConfig]:
        """Strictly validates scheduler configuration object and its boolean/integer fields."""
        enable_on_startup = cast(Optional[bool], scheduler_data.get("enable_on_startup"))
        if not isinstance(enable_on_startup, bool):
            print(
                f"\033[31m[CRITICAL ERROR]\033[0m The 'scheduler.enable_on_startup' field is mandatory and "
                f"must be a strict boolean (true/false), received: {type(enable_on_startup).__name__}."
            )
            return None

        interval_minutes = cast(Optional[int], scheduler_data.get("interval_minutes"))
        if not isinstance(interval_minutes, int) or isinstance(interval_minutes, bool):
            print(
                f"\033[31m[CRITICAL ERROR]\033[0m The 'scheduler.interval_minutes' field is mandatory and "
                f"must be an integer, received: {type(interval_minutes).__name__}."
            )
            return None

        return {
            "enable_on_startup": enable_on_startup,
            "interval_minutes": interval_minutes,
        }

    def load_configs(self) -> Tuple[Optional[Path], int, Optional[Path], SchedulerConfig]:
        """
        Validates and loads config.json settings with strict runtime type checking
        and explicit type casting to avoid unknown types under strict type checkers.
        """
        print(f"\033[34m[INFO]\033[0m System base directory: {self.base_directory}")

        raw_config = self._read_json_file(self.config_path)
        if not raw_config:
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}

        app_config = cast(AppConfig, raw_config)

        # 1. Validate path settings
        if "path" not in app_config:
            print(f"\033[31m[CRITICAL ERROR]\033[0m The mandatory 'path' field is missing in config.json.")
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}

        path_data: Any = app_config.get("path")
        if not isinstance(path_data, dict):
            print(f"\033[31m[CRITICAL ERROR]\033[0m The 'path' field must be a JSON object.")
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}

        path_result = self._validate_path_config(cast(Dict[str, Any], path_data))
        if not path_result:
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}
        root_download_dir, cookies_path = path_result

        # 2. Validate cooldown settings
        if "cooldown_minutes" not in app_config:
            print(f"\033[31m[CRITICAL ERROR]\033[0m The mandatory 'cooldown_minutes' field is missing in config.json.")
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}

        cooldown_minutes = self._validate_cooldown(app_config.get("cooldown_minutes"))
        if cooldown_minutes is None:
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}

        # 3. Validate scheduler settings
        if "scheduler" not in app_config:
            print(f"\033[31m[CRITICAL ERROR]\033[0m The mandatory 'scheduler' field is missing in config.json.")
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}

        scheduler_data: Any = app_config.get("scheduler")
        if not isinstance(scheduler_data, dict):
            print(f"\033[31m[CRITICAL ERROR]\033[0m The 'scheduler' field must be a JSON object.")
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}

        scheduler_config = self._validate_scheduler_config(scheduler_data)
        if not scheduler_config:
            return None, 0, None, {"enable_on_startup": False, "interval_minutes": 0}

        print(f"\033[34m[INFO]\033[0m Root downloads directory: {root_download_dir.resolve()}")

        return root_download_dir, cooldown_minutes, cookies_path, scheduler_config

    def load_channels(self) -> List[BaseChannelConfig]:
        """Loads the generic list of channels that extend BaseChannelConfig."""
        channels_data = self._read_json_file(self.channels_path)
        if not channels_data:
            return []

        channels: List[BaseChannelConfig] = cast(List[BaseChannelConfig], channels_data.get("channels", []))
        if not channels:
            print("\033[34m[INFO]\033[0m No channels configured in the channels.json file.")
            return []

        return channels

    def check_cooldown(self, channel_config: BaseChannelConfig, cooldown_minutes: int, now: datetime) -> bool:
        """Checks whether the channel is in a cooldown period. Returns True if the channel should be SKIPPED."""
        last_checked_str: Optional[str] = channel_config.get("last_checked")
        name: str = channel_config.get("name", "Channel")

        if cooldown_minutes <= 0:
            print("\033[33m[WARNING]\033[0m Cooldown is disabled; all channels will be analyzed.")
            return False

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
        """Saves the updated state back to channels.json."""
        try:
            channels_data = {"channels": channels}
            with open(self.channels_path, "w", encoding="utf-8") as f:
                json.dump(channels_data, f, indent=4, ensure_ascii=False)
                print(f"\n\033[34m[MEMORY]\033[0m 'last_checked' state successfully updated in channels.json.")

        except Exception as e:
            print(f"\n\033[33m[WARNING]\033[0m Failed to update the channels.json file: {e}")
