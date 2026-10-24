"""
schedulers/factory.py
This factory determines the task scheduler instance based on the operating system.
"""

import sys
from schedulers.base import BaseScheduler
from schedulers.windows import WindowsScheduler
from schedulers.linux import LinuxScheduler
from schedulers.mac import MacScheduler


class SchedulerFactory:

    @staticmethod
    def get_scheduler() -> BaseScheduler:
        if sys.platform.startswith("win"):
            return WindowsScheduler()
        elif sys.platform.startswith("linux"):
            return LinuxScheduler()
        elif sys.platform.startswith("darwin"):
            return MacScheduler()
        else:
            raise OSError(f"Unsupported operating system: {sys.platform}")
