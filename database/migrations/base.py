from abc import ABC, abstractmethod
import sqlite3


class Migration(ABC):
    """
    Abstract Base Class defining the mandatory contract for all database migrations.
    Enforces static type safety and structural compliance across schema versions.
    """

    @abstractmethod
    def upgrade(self, conn: sqlite3.Connection) -> None:
        pass
