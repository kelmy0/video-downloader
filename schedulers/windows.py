import sys
import subprocess
import os
from pathlib import Path
from schedulers.base import BaseScheduler
from typing import Optional
from utils.path_utils import PathUtils


class WindowsScheduler(BaseScheduler):
    TASK_NAME = "MediaArchiverTask"

    def _get_startup_folder(self) -> Optional[Path]:
        """Returns the path of the current user's Startup folder."""
        appdata = os.environ.get("APPDATA")
        if not appdata:
            return None

        return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"

    def _get_execution_command(self) -> str:
        """Returns the complete command formatted for Windows."""
        is_compiled = getattr(sys, "frozen", False)
        if is_compiled:
            return f'"{sys.executable}"'

        python_exe = sys.executable
        main_script = Path(sys.argv[0]).resolve()
        return f'"{python_exe}" "{main_script}"'

    def remove_schedule(self) -> bool:
        try:
            # Remove the task if it already exists (ignore error if it does not exist)
            print(f"\033[34m[INFO]\033[0m Removing possible previously scheduled tasks.")
            cmd = ["schtasks", "/delete", "/tn", f"{self.TASK_NAME}_Interval", "/f"]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

            startup_path = self._get_startup_folder()

            if startup_path:
                shortcut_path = startup_path / f"{self.TASK_NAME}.bat"

                if shortcut_path.exists():
                    shortcut_path.unlink()

            else:
                print(f"\033[33m[WARNING]\033[0m Unable to locate startup folder.")

            return True
        except Exception:
            return False

    def setup_schedule(self, interval_minutes: int, run_on_startup: bool) -> bool:
        self.remove_schedule()

        exec_cmd = self._get_execution_command()
        success = True

        if interval_minutes > 0:
            print(f"\033[34m[INFO]\033[0m scheduling execution in task scheduler every {interval_minutes} minutes.")
            cmd_interval = [
                "schtasks",
                "/create",
                "/tn",
                f"{self.TASK_NAME}_Interval",
                "/tr",
                exec_cmd,
                "/sc",
                "MINUTE",
                "/mo",
                str(interval_minutes),
                "/f",
            ]
            res = subprocess.run(cmd_interval, capture_output=True, text=True)
            if res.returncode != 0:
                print(f"\033[31m[ERROR]\033[0m Fail scheduling task every {interval_minutes} minutes.")
                success = False
            else:
                print(f"\033[32m[SUCCESS]\033[0m Task scheduled every {interval_minutes} minutes.")

        if run_on_startup:
            try:
                startup_folder = self._get_startup_folder()

                if startup_folder:
                    startup_folder.mkdir(parents=True, exist_ok=True)
                    bat_path = startup_folder / f"{self.TASK_NAME}.bat"
                    project_dir = PathUtils.get_project_root()
                    bat_content = f"@echo off\n" f'cd /d "{project_dir}"\n' f'start /min "" {exec_cmd}\n'
                    bat_path.write_text(bat_content, encoding="utf-8")
                    print(f"\033[32m[SUCCESS]\033[0m Startup hook registered successfully.")
            except Exception as e:
                print(f"\033[31m[ERROR]\033[0m Failed to register startup hook: {e}")
                success = False

        return success
