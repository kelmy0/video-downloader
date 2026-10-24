"""
main.py

Orquestrador principal do sistema de arquivamento digital.
Lê a configuração dos canais, gerencia o mapeamento de pastas e executa
o fluxo de verificação de feeds e downloads automatizados.
"""

from typing import Dict
from core.base import PlatformExtractor
from core.orchestrator import ChannelArchiverOrchestrator
from extractors.youtube import YouTubeExtractor
from config.manager import ConfigManager


def carregar_extratores() -> Dict[str, PlatformExtractor]:
    extratores = [
        YouTubeExtractor(),
    ]
    return {extrator.name: extrator for extrator in extratores}


def main() -> None:
    config_manager = ConfigManager()
    extratores = carregar_extratores()

    # Instancia o orquestrador isolado
    print(f"\033[36m==================================================\033[0m")
    print(f"\033[1m     ARCHIVER SYSTEM - INICIANDO ROTINA DE CANAIS   \033[0m")
    print(f"\033[36m==================================================\033[0m")

    orquestrador = ChannelArchiverOrchestrator(config_manager, extratores)

    orquestrador.executar()

    print(f"\n\033[32m==================================================\033[0m")
    print(f"\033[1m       ROTINA DE ARQUIVAMENTO CONCLUÍDA           \033[0m")
    print(f"\033[32m==================================================\033[0m")


if __name__ == "__main__":
    main()
