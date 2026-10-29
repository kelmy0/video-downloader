"""
core/downloader.py

Module responsible for managing the secure execution of yt_dlp,
controlling the working directory, handling errors,
and displaying real-time logs in the console.
"""

import yt_dlp
import sys
from pathlib import Path
from typing import Dict, Tuple, Any, cast


class MediaDownloader:
    """
    Centralized manager for executing external download commands.
    """

    @staticmethod
    def execute(ydl_opts: Dict[str, object], output_dir: Path) -> Tuple[bool, Dict[str, Any]]:
        """
        Performs the download using the yt-dlp Python API, returning a tuple
        containing success status and a dictionary with captured metadata info.

        Returns:
            Tuple[bool, Dict[str, Any]]: (success_status, metadata_info)
        """

        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n\033[34m[DOWNLOADER]\033[0m Running on: \033[1m{output_dir.resolve()}\033[0m")

        target_url = str(ydl_opts.pop("target_url", ""))
        if not target_url:
            print(
                f"\033[31m[DOWNLOADER] [CRITICAL ERROR]\033[0m No target URL was provided in the yt-dlp options.",
                file=sys.stderr,
            )
            return False, {}

        print(f"\n\033[34m[DOWNLOADER]\033[0m Starting yt-dlp engine for the URL: \033[36m{target_url}\033[0m")

        metadata_info: Dict[str, Any] = {}

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                info = ydl.extract_info(target_url, download=True)
                if info:
                    metadata_info = cast(Dict[str, Any], info)

            print(f"\033[32m[DOWNLOADER] [SUCCESS]\033[0m Process completed successfully.")
            return True, metadata_info

        except Exception as e:
            print(
                f"\033[31m[DOWNLOADER] [CRITICAL ERROR]\033[0m Failed to perform the download via yt-dlp: {e}",
                file=sys.stderr,
            )
            return False, {}
