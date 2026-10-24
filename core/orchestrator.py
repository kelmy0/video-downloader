"""
core/orchestrator.py

Módulo responsável por gerenciar a execução da varredura de canais,
validação de cooldown, chamadas aos extratores e execução dos downloads.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from core.base import PlatformExtractor, FetchOptions
from core.downloader import MediaDownloader
from core.dependencies import DependencyChecker
from config.manager import ConfigManager
from schemas.channel_schema import BaseChannelConfig


class ChannelArchiverOrchestrator:
    """Orquestrador do ciclo de vida de arquivamento dos canais."""

    def __init__(self, config_manager: ConfigManager, extratores: Dict[str, PlatformExtractor]) -> None:
        self.config_manager = config_manager
        self.extratores = extratores

    def _carregar_ids_arquivados(self, archive_path: Path) -> Set[Tuple[str, str]]:
        """
        Lê o archive.txt do yt-dlp e retorna um conjunto (set) apenas com os IDs
        dos vídeos já baixados, garantindo busca O(1) ultra-rápida.
        """
        ids_baixados: Set[Tuple[str, str]] = set()
        if not archive_path.exists():
            return ids_baixados

        try:
            with open(archive_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        platform = parts[0].lower()
                        video_id = parts[1]
                        ids_baixados.add((platform, video_id))
        except Exception as e:
            print(f"\033[33m[AVISO]\033[0m Falha ao ler o arquivo archive.txt: {e}")

        return ids_baixados

    def executar(self) -> None:
        # Verifica as dependencias do projeto
        if not DependencyChecker.validate_enviroment():
            return

        root_download_dir, cooldown_minutes, cookies_path = self.config_manager.carregar_configuracoes()
        if not root_download_dir:
            return

        channels: List[BaseChannelConfig] = self.config_manager.carregar_canais()
        if not channels:
            return

        agora: datetime = datetime.now()
        houve_alteracao_nos_canais: bool = False

        for idx, channel_config in enumerate(channels, start=1):
            name = channel_config.get("name", f"Canal_{idx}")
            platform_name = channel_config.get("platform", "").lower()
            feed_url = channel_config.get("feed_url")
            folder_name = channel_config.get("folder_name")

            print(f"\n\033[36m--------------------------------------------------\033[0m")
            print(f"\033[1m[{idx}/{len(channels)}] Processando: {name} (Plataforma: {platform_name})\033[0m")
            print(f"\033[36m--------------------------------------------------\033[0m")

            # Validação de Cooldown
            if self.config_manager.verificar_cooldown(channel_config, cooldown_minutes, agora):
                continue

            if not platform_name or not feed_url or not folder_name:
                print(f"\033[33m[AVISO]\033[0m Configuração incompleta para o canal '{name}'. Ignorando.")
                continue

            extrator = self.extratores.get(platform_name)
            if not extrator:
                print(f"\033[33m[AVISO]\033[0m Plataforma '{platform_name}' não suportada ou não registrada.")
                continue

            output_dir = root_download_dir / folder_name
            archive_path = output_dir / "archive.txt"

            print(f"\033[34m[INFO]\033[0m Pasta de destino: {output_dir.resolve()}")

            # 1. Carrega os pares (plataforma, id) já baixados do disco
            pares_ja_baixados = self._carregar_ids_arquivados(archive_path)

            # 2. Extrai as opções específicas da plataforma
            options: FetchOptions = extrator.extrair_opcoes(channel_config)

            # 3. Pega todos os itens do feed
            items = extrator.fetch_new_items(feed_url, options=options)

            channel_config["last_checked"] = agora.strftime("%Y-%m-%d %H:%M:%S")
            houve_alteracao_nos_canais = True

            if not items:
                print(f"\033[34m[INFO]\033[0m Nenhum item retornado pelo feed para '{name}'.")
                continue

            # 4. OTIMIZAÇÃO COM MULTI-PLATAFORMA: Valida combinando a plataforma atual e o ID do item
            nome_plataforma = extrator.name.lower()
            itens_novos = [item for item in items if (nome_plataforma, item.id) not in pares_ja_baixados]
            total_ignorados = len(items) - len(itens_novos)

            print(
                f"\033[34m[INFO]\033[0m Total no feed: {len(items)} | Já baixados: {total_ignorados} | \033[32mNovos para baixar: {len(itens_novos)}\033[0m"
            )

            if not itens_novos:
                print(f"\033[32m[INFO]\033[0m Nenhum vídeo novo para processar neste canal.")
                continue

            for item in items:
                print(f"\n\033[33m[PROCESSANDO ITEM]\033[0m {item.title} (ID: {item.id})")

                command = extrator.get_download_command(
                    item_url=item.url, output_dir=output_dir, archive_path=archive_path, cookies_path=cookies_path
                )
                sucesso = MediaDownloader.execute(command, output_dir)

                if not sucesso:
                    print(f"\033[31m[ERRO]\033[0m O download do item {item.id} falhou ou foi ignorado.")

        if houve_alteracao_nos_canais:
            self.config_manager.salvar_alteracoes_canais(channels)
