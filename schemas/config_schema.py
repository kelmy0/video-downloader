"""
schemas/config_schema.py

Schema definitions for the configuration file (config.json).
"""

from typing import TypedDict, NotRequired


class PathConfig(TypedDict):
    """Schema for path configurations."""

    download_path: str
    cookies_path: NotRequired[str]


class SchedulerConfig(TypedDict):
    """Schema for task scheduler configurations."""

    enable_on_startup: bool
    interval_minutes: int


class AppConfig(TypedDict):
    """Schema for main application configurations."""

    path: PathConfig
    cooldown_minutes: int
    scheduler: SchedulerConfig
