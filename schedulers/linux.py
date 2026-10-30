"""
schedulers/linux.py

Linux implementation of the BaseScheduler interface using user-level
XDG Autostart for startup hooks and crontab for interval scheduling.
"""

import os
import sys
import subprocess
from pathlib import Path
from schedulers.base import BaseScheduler


class LinuxScheduler(BaseScheduler):
    """Linux task scheduler managing user crontab jobs and XDG autostart entries."""

    TASK_NAME = "MediaArchiverTask"
    CRONTAB_COMMENT = "# Managed by MediaArchiverTask"

    def _get_autostart_dir(self) -> Path:
        """Returns the XDG autostart directory for the current user."""
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_dir = Path(xdg_config)
        else:
            config_dir = Path.home() / ".config"
        return config_dir / "autostart"

    def _get_execution_command(self) -> str:
        """Returns the complete command formatted for Linux execution."""
        is_compiled = getattr(sys, "frozen", False)
        if is_compiled:
            return f'"{sys.executable}"'

        python_exe = sys.executable
        main_script = Path(sys.argv[0]).resolve()
        return f'"{python_exe}" "{main_script}"'

    def remove_schedule(self) -> bool:
        """Removes the cron interval job and the XDG autostart entry without root permissions."""
        try:
            print("\033[34m[INFO]\033[0m Removing possible previously scheduled tasks on Linux.")

            # 1. Clean up user crontab
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.splitlines()
                new_lines = [line for line in lines if self.CRONTAB_COMMENT not in line]

                new_crontab = "\n".join(new_lines) + "\n" if new_lines else ""
                subprocess.run(["crontab", "-"], input=new_crontab, text=True, check=False)

            # 2. Clean up XDG autostart desktop file
            autostart_dir = self._get_autostart_dir()
            desktop_file = autostart_dir / f"{self.TASK_NAME.lower()}.desktop"
            if desktop_file.exists():
                desktop_file.unlink()

            return True
        except Exception as e:
            print(f"\033[31m[ERROR]\033[0m Failed to remove Linux schedules: {e}")
            return False

    def setup_schedule(self, interval_minutes: int, run_on_startup: bool) -> bool:
        """Sets up interval execution via crontab and startup execution via XDG autostart."""
        self.remove_schedule()

        exec_cmd = self._get_execution_command()
        success = True

        # 1. Interval scheduling via user crontab
        if interval_minutes > 0:
            print(f"\033[34m[INFO]\033[0m Scheduling execution in crontab every {interval_minutes} minutes.")
            try:
                result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, check=False)
                existing_crontab = result.stdout if result.returncode == 0 else ""

                # Format cron rule (e.g., */5 * * * *)
                cron_schedule = f"*/{interval_minutes} * * * *"
                cron_line = f"{cron_schedule} {exec_cmd} >/dev/null 2>&1 {self.CRONTAB_COMMENT}"

                new_crontab = (
                    existing_crontab.strip() + f"\n{cron_line}\n" if existing_crontab.strip() else f"{cron_line}\n"
                )

                res = subprocess.run(["crontab", "-"], input=new_crontab, text=True, capture_output=True, check=False)
                if res.returncode != 0:
                    print(f"\033[31m[ERROR]\033[0m Failed to schedule task in crontab: {res.stderr.strip()}")
                    success = False
                else:
                    print(f"\033[32m[SUCCESS]\033[0m Task scheduled in crontab every {interval_minutes} minutes.")
            except Exception as e:
                print(f"\033[31m[ERROR]\033[0m Failed to configure crontab: {e}")
                success = False

        # 2. Startup scheduling via XDG Autostart (.desktop file)
        if run_on_startup:
            try:
                autostart_dir = self._get_autostart_dir()
                autostart_dir.mkdir(parents=True, exist_ok=True)

                desktop_file = autostart_dir / f"{self.TASK_NAME.lower()}.desktop"
                desktop_content = (
                    f"[Desktop Entry]\n"
                    f"Type=Application\n"
                    f"Name=Media Archiver\n"
                    f"Exec={exec_cmd}\n"
                    f"Terminal=false\n"
                    f"X-GNOME-Autostart-enabled=true\n"
                    f"NoDisplay=true\n"
                )
                desktop_file.write_text(desktop_content, encoding="utf-8")
                print(f"\033[32m[SUCCESS]\033[0m Linux startup hook registered successfully via XDG Autostart.")
            except Exception as e:
                print(f"\033[31m[ERROR]\033[0m Failed to register Linux startup hook: {e}")
                success = False

        return success
