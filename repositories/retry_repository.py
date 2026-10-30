from database.connection import DatabaseConnection
from typing import List, Any, Dict


class RetryRepository:
    """
    Repository managing the suboptimal media download queue and retry pipeline states using SQLite.
    """

    @staticmethod
    def add_retry_item(platform: str, video_id: str, item_url: str, folder_name: str, title: str) -> bool:
        try:
            with DatabaseConnection.get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR IGNORE INTO retries (platform, video_id, item_url, folder_name, title)
                    VALUES (?, ?, ?, ?, ?);
                """,
                    (platform, video_id, item_url, folder_name, title),
                )
            return True
        except Exception as e:
            print(f"\033[31m[DB ERROR]\033[0m Failed to add retry item: {e}")
            return False

    @staticmethod
    def get_retries() -> List[Dict[str, Any]]:
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.execute("SELECT platform, video_id, item_url, folder_name, title FROM retries")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def remove_retry_item(video_id: str, platform: str) -> bool:
        try:
            with DatabaseConnection.get_connection() as conn:
                conn.execute(
                    """
                    DELETE FROM retries WHERE video_id = ? AND platform = ?;
                """,
                    (video_id, platform),
                )
            return True
        except Exception as e:
            print(f"\033[31m[DB ERROR]\033[0m Failed to remove retry item: {e}")
            return False
