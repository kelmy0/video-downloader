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
    """Loads and returns a dictionary of registered platform extractors."""
    extractors = [
        YouTubeExtractor(),
    ]
    return {extractor.name: extractor for extractor in extractors}


def main() -> None:
    """Main entry point for the archiving routine."""
    config_manager = ConfigManager()
    extractors = load_extractors()

    print("\033[36m=============================================\033[0m")
    print("\033[1m             STARTING ARCHIVING ROUTINE             \033[0m")
    print("\033[36m=============================================\033[0m")

    orchestrator = ChannelArchiverOrchestrator(config_manager, extractors)
    orchestrator.run()

    print("\n\033[32m==============================================\033[0m")
    print("\033[1m             ARCHIVING ROUTINE COMPLETED             \033[0m")
    print("\033[32m==============================================\033[0m")


if __name__ == "__main__":
    main()
