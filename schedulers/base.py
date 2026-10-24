from abc import ABC, abstractmethod


class BaseScheduler(ABC):
    """
    Abstract interface for the task scheduler across different operating systems.
    """

    @abstractmethod
    def setup_schedule(self, interval_minutes: int, run_on_startup: bool) -> bool:
        """Configures or updates the scheduled task in the operating system."""
        pass

    @abstractmethod
    def remove_schedule(self) -> bool:
        """Removes the scheduled task from the operating system."""
        pass
