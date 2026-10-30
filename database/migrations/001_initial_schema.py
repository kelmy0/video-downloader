import sqlite3
from database.migrations.base import Migration


class InitialSchemaMigration(Migration):
    """
    Initial database schema migration.
    Creates the core 'retries' table and primary keys for suboptimal media tracking.
    """

    def upgrade(self, conn: sqlite3.Connection) -> None:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS retries (
                platform TEXT NOT NULL,
                video_id TEXT NOT NULL,
                item_url TEXT NOT NULL,
                folder_name TEXT NOT NULL,
                title TEXT NOT NULL,
                PRIMARY KEY (platform, video_id)
            );
        """)
