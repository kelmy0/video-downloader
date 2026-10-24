"""
main.py

loads extractors, create instances and invokes methods to run the project.
"""

from typing import Dict, Any
from core.base import PlatformExtractor
from core.orchestrator import ChannelArchiverOrchestrator
from extractors.youtube import YouTubeExtractor
from config.manager import ConfigManager


def load_extractors() -> Dict[str, PlatformExtractor[Any]]:
    extractors = [
        YouTubeExtractor(),
    ]
    return {extrator.name: extrator for extrator in extractors}


def main() -> None:
    config_manager = ConfigManager()
    extractors = load_extractors()

    print(f"\033[36m=============================================\033[0m")
    print(f"\033[1m          STARTING ARCHIVING ROUTINE          \033[0m")
    print(f"\033[36m=============================================\033[0m")

    orquestrador = ChannelArchiverOrchestrator(config_manager, extractors)

    orquestrador.executar()

    print(f"\n\033[32m==============================================\033[0m")
    print(f"\033[1m          ARCHIVING ROUTINE COMPLETED          \033[0m")
    print(f"\033[32m==============================================\033[0m")


if __name__ == "__main__":
    main()
