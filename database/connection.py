import sqlite3
from pathlib import Path
from utils.path_utils import PathUtils


class DatabaseConnection:
    """
    Centralized SQLite connection manager.
    Resolves local file paths securely within the unversioned storage directory and configures row factories.
    """

    @staticmethod
    def __get_db_path() -> Path:
        storage_dir = PathUtils.get_project_root() / "storage"
        storage_dir.mkdir(parents=True, exist_ok=True)
        return storage_dir / "archiver.db"

    @staticmethod
    def get_connection() -> sqlite3.Connection:
        db_path = DatabaseConnection.__get_db_path()
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
