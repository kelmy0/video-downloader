"""
schedulers/factory.py
This factory determines the task scheduler instance based on the operating system.
"""

import sys
from .base import BaseScheduler
from .windows import WindowsScheduler


class SchedulerFactory:

    @staticmethod
    def get_scheduler() -> BaseScheduler:
        if sys.platform.startswith("win"):
            return WindowsScheduler()
        elif sys.platform.startswith("linux"):
            # return LinuxScheduler()
            raise NotImplementedError("Linux scheduler not implemented yet.")
        elif sys.platform.startswith("darwin"):
            # return MacScheduler()
            raise NotImplementedError("macOS scheduler not implemented yet.")
        else:
            raise OSError(f"Unsupported operating system: {sys.platform}")
