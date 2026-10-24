"""
schemas/channel_schema.py
schema of channels.json file
"""

from typing import TypedDict, List, TypeVar, Generic


class BaseChannelConfig(TypedDict, total=False):
    """Common fields to any channel on any platform."""

    name: str
    platform: str
    feed_url: str
    folder_name: str
    last_checked: str
    fetch_videos: bool


class YouTubeChannelConfig(BaseChannelConfig, total=False):
    """Specific configuration for YouTube channels."""

    fetch_shorts: bool


# class BilibiliChannelConfig(BaseChannelConfig, total=False):
#     fetch_dynamic: bool

# class VKChannelConfig(BaseChannelConfig, total=False):
#     fetch_clips: bool


T_Channel = TypeVar("T_Channel", bound=BaseChannelConfig)


class ChannelsFileSchema(TypedDict, Generic[T_Channel]):
    channels: List[T_Channel]
