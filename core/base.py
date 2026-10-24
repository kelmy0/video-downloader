from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, TypedDict, Dict
from config.manager import BaseChannelConfig


@dataclass(frozen=True)
class MediaItem:
    """
    Data Transfer Object (DTO) imutável para padronizar os dados de mídias
    obtidos de qualquer plataforma (YouTube, Bilibili, etc.).
    """

    id: str  # Identificador único do vídeo/post na plataforma de origem.
    title: str  # Título do conteúdo.
    url: str  # URL direta para acesso ou download do vídeo/post.
    extractor: str  # Nome identificador do extrator (ex: 'youtube', 'bilibili').
    upload_date: Optional[str] = None  # Data de publicação (formato YYYYMMDD ou ISO, se disponível).


class FetchOptions(TypedDict, total=False):
    """Tipagem estrita para opções adicionais de busca nos feeds."""

    fetch_videos: bool
    fetch_shorts: bool


class PlatformExtractor(ABC):
    """
    Classe Abstrata de Base (Interface) que define o contrato obrigatório
    que qualquer novo extrator de plataforma deve implementar.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Nome identificador único da plataforma (ex: 'youtube', 'bilibili').
        Usado para validações e correspondência no arquivo de configuração.

        Returns:
            str: O identificador simples da plataforma.
        """
        pass

    @abstractmethod
    def fetch_new_items(self, target_feed: str, options: Optional[FetchOptions] = None) -> List[MediaItem]:
        """
        Efetua a leitura do feed leve da plataforma.
        Args:
            target_feed (str): URL do canal ou feed.
            options (Optional[FetchOptions]): Opções adicionais de busca (ex: vídeos, shorts).
        """
        pass

    @abstractmethod
    def get_download_command(
        self, item_url: str, output_dir: Path, archive_path: Path, cookies_path: Optional[Path] = None
    ) -> Dict[str, object]:
        """
        Constrói o dicionário de opções tipadas do yt-dlp para realizar o download.

        Args:
            item_url (str): URL do vídeo a ser baixado.
            output_dir (Path): Caminho da pasta física onde o arquivo será salvo.
            archive_path (Path): Caminho do arquivo archive.txt localizado dentro da pasta.
            cookies_path (Optional[Path]): Caminho opcional para o arquivo de cookies.

        Returns:
            Dict[str, object]: Dicionário de configuração nativa para o yt_dlp.YoutubeDL.
        """
        pass

    @abstractmethod
    def extrair_opcoes(self, channel_config: BaseChannelConfig) -> FetchOptions:
        """Extrai as opções específicas a partir da configuração genérica do canal."""
        pass
