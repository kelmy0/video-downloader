from database.connection import DatabaseConnection


class ImportedFolderRepository:
    """Repository managing the tracking of imported folders."""

    @staticmethod
    def is_folder_imported(folder_name: str) -> bool:
        """
        Checks if a given folder has already been imported into the SQLite database.
        Returns True if the folder was already scanned, False otherwise.
        """
        with DatabaseConnection.get_connection() as conn:
            cursor = conn.execute(
                "SELECT 1 FROM imported_folders WHERE folder_name = ?;",
                (folder_name,),
            )
            return cursor.fetchone() is not None

    @staticmethod
    def mark_folder_as_imported(folder_name: str) -> None:
        """
        Marks a folder as successfully imported.
        """
        with DatabaseConnection.get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO imported_folders (folder_name)
                VALUES (?);
                """,
                (folder_name,),
            )
