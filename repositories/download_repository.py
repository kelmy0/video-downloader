from database.connection import DatabaseConnection
from typing import Set, Tuple, List


class DownloadRepository:

    @staticmethod
    def get_download_history() -> Set[Tuple[str, str]]:
        """
        Retrieves all downloaded media records from the database and
        returns them as Set of tuples (platform, video_id).
        """
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.execute("SELECT platform, video_id FROM download_history;")
            rows = cursor.fetchall()
            return set((row["platform"], row["video_id"]) for row in rows)

    @staticmethod
    def add_download_item(platform: str, video_id: str) -> None:
        """Adds a single, newly downloaded video to the global history."""
        with DatabaseConnection.get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO download_history (platform, video_id)
                VALUES (?, ?);
                """,
                (platform, video_id),
            )

    @staticmethod
    def add_download_items_batch(items: List[Tuple[str, str]]) -> None:
        """Adds multiple videos in a batch."""
        if not items:
            return

        with DatabaseConnection.get_connection() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO download_history (platform, video_id)
                VALUES (?, ?);
                """,
                (items),
            )
