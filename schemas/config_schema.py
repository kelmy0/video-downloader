"""
schemas/config_schema.py
schema of config.json file
"""

from typing import TypedDict, NotRequired


class PathConfig(TypedDict):
    download_path: str
    cookies_path: NotRequired[str]


class SchedulerConfig(TypedDict, total=False):
    enable_on_startup: bool
    interval_minutes: int


class AppConfig(TypedDict):
    path: PathConfig
    cooldown_minutes: int
    scheduler: SchedulerConfig
