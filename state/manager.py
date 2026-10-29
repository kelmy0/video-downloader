import json
from pathlib import Path
from typing import Dict, List, Any
from utils.path_utils import PathUtils


class StateManager:
    """Manages runtime application state, such as low-quality or failed items pending retry."""

    @staticmethod
    def _get_state_file() -> Path:
        """Retorna o caminho absoluto do arquivo de estado na raiz do projeto."""
        state_dir = PathUtils.get_project_root() / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        return state_dir / "low_quality.json"

    @staticmethod
    def _load_data() -> Dict[str, List[Dict[str, Any]]]:
        state_file = StateManager._get_state_file()
        if not state_file.exists():
            return {"retries": []}
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"retries": []}

    @staticmethod
    def _save_data(data: Dict[str, List[Dict[str, Any]]]) -> None:
        state_file = StateManager._get_state_file()
        try:
            with open(state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"\033[31m[ERROR]\033[0m Failed to save state file: {e}")

    @staticmethod
    def add_retry_item(platform: str, video_id: str, item_url: str, folder_name: str, title: str) -> None:
        data = StateManager._load_data()

        exists = any(item["video_id"] == video_id and item["platform"] == platform for item in data["retries"])
        if not exists:
            data["retries"].append(
                {
                    "platform": platform,
                    "video_id": video_id,
                    "item_url": item_url,
                    "folder_name": folder_name,
                    "title": title,
                }
            )
            StateManager._save_data(data)

    @staticmethod
    def get_retries() -> List[Dict[str, Any]]:
        return StateManager._load_data().get("retries", [])

    @staticmethod
    def remove_retry_item(video_id: str, platform: str) -> None:
        data = StateManager._load_data()
        data["retries"] = [
            item for item in data["retries"] if not (item["video_id"] == video_id and item["platform"] == platform)
        ]
        StateManager._save_data(data)
