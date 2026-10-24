"""
extractors/youtube.py

Implementação do extrator para a plataforma YouTube, utilizando
o feed RSS XML nativo para varredura leve de novos vídeos.
"""

import yt_dlp

from pathlib import Path
from typing import List, Optional, Set, Tuple, cast, Dict
from core.base import PlatformExtractor, FetchOptions, MediaItem
from config.manager import BaseChannelConfig
from schemas.channel_schema import YouTubeChannelConfig


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

        ydl_opts: Dict[str, object] = {
            "extract_flat": True,
            "skip_download": True,
            "no_warnings": True,
            "quiet": True,
        }

        for endpoint, tipo in endpoints_a_varrer:
            print(f"\033[34m[YouTubeExtractor]\033[0m Varredura leve ({tipo}) no canal: {endpoint}")

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                    info = ydl.extract_info(endpoint, download=False)

                    if not info:
                        print(
                            f"\033[33m[YouTubeExtractor] [AVISO]\033[0m Falha ao varrer a aba {tipo}: Nenhum dado retornado."
                        )
                        continue

                    entries = info.get("entries", [info])

                    if not entries:
                        continue

                    for entry in entries:
                        if not entry:
                            continue

                        video_id = entry.get("id")
                        title = entry.get("title")

                        if video_id and title and video_id not in seen_ids:
                            seen_ids.add(video_id)
                            url = f"https://www.youtube.com/watch?v={video_id}"
                            upload_date = entry.get("upload_date")

                            all_items.append(
                                MediaItem(
                                    id=video_id, title=title, url=url, extractor=self.name, upload_date=upload_date
                                )
                            )
            except Exception as e:
                print(f"\033[31m[YouTubeExtractor] [ERRO]\033[0m Erro ao varrer {tipo}: {e}")

        print(f"\033[32m[YouTubeExtractor] [SUCESSO]\033[0m Total de {len(all_items)} itens únicos encontrados.")

        return all_items

    def get_download_command(
        self, item_url: str, output_dir: Path, archive_path: Path, cookies_path: Optional[Path] = None
    ) -> Dict[str, object]:
        """
        Constrói o dicionário de opções padrão do yt-dlp mantendo a preferência
        de qualidade, salvando metadados e miniaturas nativamente.
        """

        ydl_opts: Dict[str, object] = {
            "format": "bestvideo*+bestaudio/best",
            "merge_output_format": "mkv",
            "writeinfojson": True,
            "writethumbnail": True,
            "embedthumbnail": True,
            "embedmetadata": True,
            "embedsubs": True,
            "writesubtitles": True,
            "subtitleslangs": ["all"],
            "paths": {"home": str(output_dir.resolve())},
            "download_archive": str(archive_path.resolve()),
        }

        if cookies_path and cookies_path.exists():
            ydl_opts["cookiefile"] = str(cookies_path.resolve())

        ydl_opts["url_alvo"] = item_url

        return ydl_opts

    def extrair_opcoes(self, channel_config: BaseChannelConfig) -> FetchOptions:
        yt_config = cast(YouTubeChannelConfig, channel_config)

        return {
            "fetch_videos": yt_config.get("fetch_videos", True),
            "fetch_shorts": yt_config.get("fetch_shorts", False),
        }
