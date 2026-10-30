"""
core/dependencies.py

Module responsible for verifying the integrity and presence
of external dependencies (yt-dlp and ffmpeg) on ​​the system.
"""

import shutil
from pathlib import Path
from typing import Optional


class DependencyChecker:
    """Checker for system dependencies required for archiving."""

    @staticmethod
    def check_bin(bin_name: str) -> Optional[Path]:
        """
        Checks whether an executable is available in the system PATH.
        Returns the absolute path to the binary if found, or None otherwise.
        """
        path = shutil.which(bin_name)
        return Path(path) if path else None

    @classmethod
    def validate_enviroment(cls) -> bool:
        """
        Verifies that all essential tools are installed.
        """
        print(f"\033[36m[INFO]\033[0m Checking system dependencies...")

        ffmpeg_path = cls.check_bin("ffmpeg")

        if not ffmpeg_path:
            print(f"\033[33m[CRITICAL ERROR]\033[0m 'ffmpeg' not found.")
            return False

        print(f"\033[32m[OK]\033[0m ffmpeg found at: {ffmpeg_path}")

        return True
