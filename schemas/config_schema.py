"""
schemas/config_schema.py
schema of config.json file
"""

from typing import TypedDict


class PathConfig(TypedDict, total=False):
    download_path: str
    cookies_path: str


class SchedulerConfig(TypedDict, total=False):
    enable_on_startup: bool
    interval_minutes: int


class AppConfig(TypedDict, total=False):
    path: PathConfig
    cooldown_minutes: int
    scheduler: SchedulerConfig
