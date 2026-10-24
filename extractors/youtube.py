"""
extractors/youtube.py

Implementation of an extractor for the YouTube platform,
utilizing the native feed for lightweight scanning of new videos.
"""

import yt_dlp

from pathlib import Path
from typing import List, Optional, Set, Tuple, cast, Dict
from core.base import PlatformExtractor, FetchOptions, MediaItem
from config.manager import BaseChannelConfig
from schemas.channel_schema import YouTubeChannelConfig


class YouTubeExtractor(PlatformExtractor):
    """
    Specialized extractor for YouTube. Reads the official RSS feed and
    returns a list of available items.
    """

    @property
    def name(self) -> str:
        return "youtube"

    def fetch_new_items(self, target_feed: str, options: Optional[FetchOptions] = None) -> List[MediaItem]:
        """
        Scans the YouTube videos and/or Shorts tabs based on the selected options.
        """

        opts: FetchOptions = options if options is not None else {}
        fetch_videos = opts.get("fetch_videos", True)
        fetch_shorts = opts.get("fetch_shorts", False)

        all_items: List[MediaItem] = []
        seen_ids: Set[str] = set()

        endpoints_to_scan: List[Tuple[str, str]] = []
        base_url = target_feed.rstrip("/")

        # If the URL is an explicit YouTube playlist, we use it directly without adding any tab suffixes.
        if "playlist?list=" in base_url or "watch?v=" in base_url:
            endpoints_to_scan.append((base_url, "Playlist/Single Media Item"))
        else:
            # Normal behavior for channels (respecting the flags)
            if "/videos" in base_url:
                base_url = base_url.replace("/videos", "")
            if "/shorts" in base_url:
                base_url = base_url.replace("/shorts", "")

            if fetch_videos:
                endpoints_to_scan.append((f"{base_url}/videos", "Videos"))
            if fetch_shorts:
                endpoints_to_scan.append((f"{base_url}/shorts", "Shorts"))

            if not endpoints_to_scan:
                endpoints_to_scan.append((f"{base_url}/videos", "Videos"))

        ydl_opts: Dict[str, object] = {
            "extract_flat": True,
            "skip_download": True,
            "no_warnings": True,
            "quiet": True,
        }

        for endpoint, tipo in endpoints_to_scan:
            print(f"\033[34m[YouTubeExtractor]\033[0m Light scan ({tipo}) on channel: {endpoint}")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                    info = ydl.extract_info(endpoint, download=False)

                    if not info:
                        print(f"\033[33m[YouTubeExtractor] [WARNING]\033[0m Fail to scan {tipo}: No data returned.")
                        continue

                    entries = info.get("entries", [info])

                    if not entries:
                        continue

                    for entry in entries:
                        if not entry:
                            continue

                        video_id = entry.get("id")
                        title = entry.get("title")

                        if video_id and title and video_id not in seen_ids:
                            seen_ids.add(video_id)
                            url = f"https://www.youtube.com/watch?v={video_id}"
                            upload_date = entry.get("upload_date")

                            all_items.append(
                                MediaItem(
                                    id=video_id, title=title, url=url, extractor=self.name, upload_date=upload_date
                                )
                            )
            except Exception as e:
                print(f"\033[31m[YouTubeExtractor] [ERROR]\033[0m Fail to scan {tipo}: {e}")

        print(f"\033[32m[YouTubeExtractor] [SUCCESS]\033[0m Total of {len(all_items)} unique items found.")

        return all_items

    def get_download_command(
        self, item_url: str, output_dir: Path, archive_path: Path, cookies_path: Optional[Path] = None
    ) -> Dict[str, object]:
        """
        Constructs the default yt-dlp options dictionary, maintaining quality
        preferences and natively saving metadata and thumbnails.
        """

        ydl_opts: Dict[str, object] = {
            "format": "bestvideo*+bestaudio/best",
            "merge_output_format": "mkv",
            "writeinfojson": True,
            "writethumbnail": True,
            "embedthumbnail": True,
            "embedmetadata": True,
            "embedsubs": True,
            "writesubtitles": True,
            "subtitleslangs": ["all"],
            "paths": {"home": str(output_dir.resolve())},
            "download_archive": str(archive_path.resolve()),
        }

        if cookies_path and cookies_path.exists():
            ydl_opts["cookiefile"] = str(cookies_path.resolve())

        ydl_opts["target_url"] = item_url

        return ydl_opts

    def extract_options(self, channel_config: BaseChannelConfig) -> FetchOptions:
        yt_config = cast(YouTubeChannelConfig, channel_config)

        return {
            "fetch_videos": yt_config.get("fetch_videos", True),
            "fetch_shorts": yt_config.get("fetch_shorts", False),
        }
