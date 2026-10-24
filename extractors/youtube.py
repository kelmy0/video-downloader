"""
extractors/youtube.py

Implementação do extrator para a plataforma YouTube, utilizando
o feed RSS XML nativo para varredura leve de novos vídeos.
"""

import subprocess
import json

from pathlib import Path
from typing import List, Optional, Set, Tuple, cast
from core.base import PlatformExtractor, FetchOptions, MediaItem
from config.manager import BaseChannelConfig
from config.schemas import YouTubeChannelConfig


class YouTubeExtractor(PlatformExtractor):
    """
    Extrator especializado para o YouTube. Lê o feed RSS oficial e
    retorna a lista de itens disponíveis.
    """

    @property
    def name(self) -> str:
        return "youtube"

    def fetch_new_items(self, target_feed: str, options: Optional[FetchOptions] = None) -> List[MediaItem]:
        """
        Varre as abas de vídeos e/ou shorts do YouTube com base nas opções tipadas.
        """

        opts: FetchOptions = options if options is not None else {}
        fetch_videos = opts.get("fetch_videos", True)
        fetch_shorts = opts.get("fetch_shorts", False)

        all_items: List[MediaItem] = []
        seen_ids: Set[str] = set()

        endpoints_a_varrer: List[Tuple[str, str]] = []
        base_url = target_feed.rstrip("/")

        # Se a URL for uma playlist explícita do YouTube, usamos ela diretamente sem adicionar sufixos de abas
        if "playlist?list=" in base_url or "watch?v=" in base_url:
            endpoints_a_varrer.append((base_url, "Playlist/Mídia Única"))
        else:
            # Comportamento normal para canais (respeitando as flags)
            if "/videos" in base_url:
                base_url = base_url.replace("/videos", "")
            if "/shorts" in base_url:
                base_url = base_url.replace("/shorts", "")

            if fetch_videos:
                endpoints_a_varrer.append((f"{base_url}/videos", "Vídeos"))
            if fetch_shorts:
                endpoints_a_varrer.append((f"{base_url}/shorts", "Shorts"))

            if not endpoints_a_varrer:
                endpoints_a_varrer.append((f"{base_url}/videos", "Vídeos"))

        for endpoint, tipo in endpoints_a_varrer:
            print(f"[YouTubeExtractor] Varredura leve ({tipo}) no canal: {endpoint}")

            command = ["yt-dlp", "--flat-playlist", "--print-json", "--no-warnings", endpoint]

            try:
                result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")

                if result.returncode != 0:
                    print(f"[YouTubeExtractor] [AVISO] Falha ao varrer a aba {tipo}: {result.stderr.strip()}")
                    continue

                for line in result.stdout.splitlines():
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        video_id = data.get("id")
                        title = data.get("title")

                        if video_id and title and video_id not in seen_ids:
                            seen_ids.add(video_id)
                            url = f"https://www.youtube.com/watch?v={video_id}"
                            upload_date = data.get("upload_date")

                            all_items.append(
                                MediaItem(
                                    id=video_id, title=title, url=url, extractor=self.name, upload_date=upload_date
                                )
                            )
                    except json.JSONDecodeError:
                        continue

            except Exception as e:
                print(f"[YouTubeExtractor] [ERRO] Erro ao varrer {tipo}: {e}")

        print(f"[YouTubeExtractor] Sucesso: Total de {len(all_items)} itens únicos encontrados.")

        return all_items

    def get_download_command(self, item_url: str, output_dir: Path, archive_path: Path) -> List[str]:
        """
        Constrói o comando CLI padrão do yt-dlp mantendo a sua preferência
        de qualidade e salvando metadados e miniaturas.
        """

        command: List[str] = [
            "yt-dlp",
            "-f",
            "bestvideo*+bestaudio/best",
            "--merge-output-format",
            "mkv",
            "--write-info-json",
            "--write-thumbnail",
            "--embed-thumbnail",
            "--embed-metadata",
            "--embed-subs",
            "--write-subs",
            "--sub-langs",
            "all",
            "--paths",
            str(output_dir.resolve()),
            "--download-archive",
            str(archive_path.resolve()),
            item_url,
        ]
        return command

    def extrair_opcoes(self, channel_config: BaseChannelConfig) -> FetchOptions:
        yt_config = cast(YouTubeChannelConfig, channel_config)

        return {
            "fetch_videos": yt_config.get("fetch_videos", True),
            "fetch_shorts": yt_config.get("fetch_shorts", False),
        }
