import sqlite3
from database.migrations.base import Migration


class InitialSchemaMigration(Migration):
    """
    Initial database schema migration.
    Creates the core 'retries' table and primary keys for suboptimal media tracking.
    """

    def upgrade(self, conn: sqlite3.Connection) -> None:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS retries (
                platform TEXT NOT NULL,
                video_id TEXT NOT NULL,
                item_url TEXT NOT NULL,
                folder_name TEXT NOT NULL,
                title TEXT NOT NULL,
                PRIMARY KEY (platform, video_id)
            );

            CREATE TABLE IF NOT EXISTS download_history (
                platform TEXT NOT NULL,
                video_id TEXT NOT NULL,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                archive_status TEXT DEFAULT 'none' CHECK(archive_status IN ('none', 'pending', 'archived', 'failed')),
                archive_url TEXT,
                PRIMARY KEY (platform, video_id)
            );

            CREATE INDEX IF NOT EXISTS idx_download_platform_video 
            ON download_history (platform, video_id);

            CREATE TABLE IF NOT EXISTS imported_folders (
                folder_name TEXT PRIMARY KEY,
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
