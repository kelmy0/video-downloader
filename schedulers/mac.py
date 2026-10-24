"""
schedulers/mac.py

macOS implementation of the BaseScheduler interface using user-level
launchd agents (~/Library/LaunchAgents/) for interval and startup scheduling.
"""

import sys
import subprocess
from pathlib import Path
from typing import List
from schedulers.base import BaseScheduler


class MacScheduler(BaseScheduler):
    """macOS task scheduler managing user-level launchd .plist agents."""

    LABEL = "com.mediaarchiver.task"

    def _get_launch_agents_dir(self) -> Path:
        """Returns the user's LaunchAgents directory."""
        return Path.home() / "Library" / "LaunchAgents"

    def _get_program_arguments(self) -> List[str]:
        """Returns the list of program arguments formatted for launchd ProgramArguments."""
        is_compiled = getattr(sys, "frozen", False)
        if is_compiled:
            return [sys.executable]

        python_exe = sys.executable
        main_script = str(Path(sys.argv[0]).resolve())
        return [python_exe, main_script]

    def remove_schedule(self) -> bool:
        """Unloads and removes the launchd agent plist file without root permissions."""
        try:
            print("\033[34m[INFO]\033[0m Removing possible previously scheduled tasks on macOS.")
            launch_agents_dir = self._get_launch_agents_dir()
            plist_path = launch_agents_dir / f"{self.LABEL}.plist"

            if plist_path.exists():
                # Unload the agent safely before deleting
                subprocess.run(
                    ["launchctl", "unload", str(plist_path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )
                plist_path.unlink()

            return True
        except Exception as e:
            print(f"\033[31m[ERROR]\033[0m Failed to remove macOS schedules: {e}")
            return False

    def setup_schedule(self, interval_minutes: int, run_on_startup: bool) -> bool:
        """Sets up interval and/or startup execution via user launchd agent plist."""
        self.remove_schedule()

        if interval_minutes <= 0 and not run_on_startup:
            return True

        try:
            launch_agents_dir = self._get_launch_agents_dir()
            launch_agents_dir.mkdir(parents=True, exist_ok=True)
            plist_path = launch_agents_dir / f"{self.LABEL}.plist"

            args = self._get_program_arguments()
            args_xml = "".join([f"        <string>{arg}</string>\n" for arg in args])

            extra_keys = ""
            if interval_minutes > 0:
                interval_seconds = interval_minutes * 60
                extra_keys += f"    <key>StartInterval</key>\n    <integer>{interval_seconds}</integer>\n"
                print(
                    f"\033[34m[INFO]\033[0m Scheduling execution in launchd every {interval_minutes} minutes ({interval_seconds}s)."
                )

            if run_on_startup:
                extra_keys += "<key>RunAtLoad</key>\n    <true/>\n"
                print(f"\033[34m[INFO]\033[0m Enabling startup execution via launchd RunAtLoad.")

            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{self.LABEL}</string>
    <key>ProgramArguments</key>
    <array>
{args_xml}    </array>
{extra_keys}    <key>StandardOutPath</key>
    <string>/dev/null</string>
    <key>StandardErrorPath</key>
    <string>/dev/null</string>
</dict>
</plist>
"""

            plist_path.write_text(plist_content, encoding="utf-8")

            # Load the agent into launchd
            res = subprocess.run(
                ["launchctl", "load", str(plist_path)],
                capture_output=True,
                text=True,
                check=False,
            )

            if res.returncode != 0:
                print(f"\033[31m[ERROR]\033[0m Failed to load launchd task: {res.stderr.strip()}")
                return False

            print(f"\033[32m[SUCCESS]\033[0m macOS launchd schedule registered successfully.")
            return True

        except Exception as e:
            print(f"\033[31m[ERROR]\033[0m Failed to configure macOS launchd schedule: {e}")
            return False
