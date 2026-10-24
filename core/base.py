from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Dict, TypeVar, Generic
from schemas.channel_schema import BaseChannelConfig


@dataclass(frozen=True)
class MediaItem:
    """
    Immutable Data Transfer Object (DTO) to standardize media data
    obtained from any platform (YouTube, Bilibili, etc.).
    """

    id: str  # Unique identifier for the video/post on the originating platform.
    title: str  # Content title.
    url: str  # Direct URL for accessing or downloading the video/post.
    extractor: str  # Extractor identifier name (e.g., 'youtube', 'bilibili').
    upload_date: Optional[str] = None  # Publication date (in YYYYMMDD or ISO format, if available).


T_Options = TypeVar("T_Options")


class PlatformExtractor(ABC, Generic[T_Options]):
    """
    Abstract Base Class (Interface) that defines the mandatory contract
    that any new platform extractor must implement.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Unique platform identifier name (e.g., 'youtube', 'bilibili').
        Used for validation and matching within the configuration file.

        Returns:
        str: The simple platform identifier.
        """
        pass

    @abstractmethod
    def fetch_new_items(self, target_feed: str, options: Optional[T_Options] = None) -> List[MediaItem]:
        """
        Reads the platform's lightweight feed.
        Args:
        target_feed (str): URL of the channel or feed.
        options (Optional[FetchOptions]): Additional fetch options (e.g., videos, shorts).
        """
        pass

    @abstractmethod
    def get_download_command(
        self, item_url: str, output_dir: Path, archive_path: Path, cookies_path: Optional[Path] = None
    ) -> Dict[str, object]:
        """
        Constructs the dictionary of typed options for yt-dlp to perform the download.

        Args:
        item_url (str): URL of the video to be downloaded.
        output_dir (Path): Path to the physical directory where the file will be saved.
        archive_path (Path): Path to the archive.txt file located within the directory.
        cookies_path (Optional[Path]): Optional path to the cookies file.

        Returns:
        Dict[str, object]: Configuration dictionary for yt_dlp.YoutubeDL.
        """
        pass

    @abstractmethod
    def extract_options(self, channel_config: BaseChannelConfig) -> T_Options:
        """Extracts specific options from the generic channel configuration."""
        pass
