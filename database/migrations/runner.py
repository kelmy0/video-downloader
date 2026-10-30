import importlib
import sqlite3
import pkgutil
import inspect
from pathlib import Path
from typing import List, Type, Optional
from database.connection import DatabaseConnection
from database.migrations.base import Migration


class MigrationRunner:
    """
    Automated migration engine.
    Discovers, tracks, and applies pending database schema updates incrementally in strict chronological order.
    """

    @staticmethod
    def _init_version_table(conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations(
                version TEXT PRIMATY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );        
        """)

    @staticmethod
    def run_pending_migrations() -> None:
        """Scans the migrations folder, identifies which ones are missing, and executes them in order."""
        with DatabaseConnection.get_connection() as conn:
            MigrationRunner._init_version_table(conn)

            cursor = conn.execute("SELECT version FROM schema_migrations;")
            applied_versions = {row["version"] for row in cursor.fetchall()}

            migrations_pkg = Path(__file__).parent
            migration_modules: List[str] = []

            for _, module_name, _ in pkgutil.iter_modules([str(migrations_pkg)]):
                if module_name not in ("runner", "base"):
                    migration_modules.append(module_name)

            migration_modules.sort()

            for mod_name in migration_modules:
                if mod_name not in applied_versions:
                    print(f"\033[36m[DB MIGRATION]\033[0m Applying migration: {mod_name}")

                    module = importlib.import_module(f"database.migrations.{mod_name}")

                    migration_class: Optional[Type[Migration]] = None
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, Migration) and obj is not Migration:
                            migration_class = obj
                            break

                    if not migration_class:
                        raise TypeError(f"Module '{mod_name}' must contain a class that inherits from 'Migration'.")

                    try:
                        migration_instance = migration_class()
                        migration_instance.upgrade(conn)

                        conn.execute("INSERT INTO schema_migrations (version) VALUES (?);", (mod_name,))
                        conn.commit()
                        print(f"\033[32m[DB MIGRATION]\033[0m Successfully applied: {mod_name}")

                    except Exception as e:
                        print(f"\033[31m[DB CRITICAL ERROR]\033[0m Migration {mod_name} failed: {e}")
                        print(f"\033[31m[DB ROLLBACK]\033[0m Aborting process to prevent database corruption.")
                        raise RuntimeError(f"Database migration failed at '{mod_name}'. Aborted.") from e
