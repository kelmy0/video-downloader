from pathlib import Path


class PathUtils:

    @staticmethod
    def get_project_root() -> Path:
        """
        Returns the actual root of the project dynamically and securely,
        regardless of where the script was called from.
        """
        current = Path(__file__).resolve()

        for parent in [current, *current.parents]:
            if (parent / "main.py").exists() or (parent / ".venv").exists():
                return parent

        return current.parent
