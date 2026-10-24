"""
config/schemas.py

Define os contratos estritos (TypedDicts) para os arquivos de configuração
do sistema, garantindo tipagem forte sem uso de Any.
"""

from typing import TypedDict, List, TypeVar, Generic


class PathConfig(TypedDict):
    """Estrutura da chave 'path' no config.json."""

    download_path: str
    cookies_path: str


class AppConfig(TypedDict, total=False):
    """Contrato estrito para o config.json."""

    path: PathConfig
    cooldown_minutes: int


class BaseChannelConfig(TypedDict, total=False):
    """Campos obrigatórios e comuns a qualquer canal em qualquer plataforma."""

    name: str
    platform: str
    feed_url: str
    folder_name: str
    last_checked: str
    fetch_videos: bool


class YouTubeChannelConfig(BaseChannelConfig, total=False):
    """Configuração específica para canais do YouTube."""

    fetch_shorts: bool


# class BilibiliChannelConfig(BaseChannelConfig, total=False):
#     fetch_dynamic: bool

# class VKChannelConfig(BaseChannelConfig, total=False):
#     fetch_clips: bool

# TypeVar restrito ao BaseChannelConfig para garantir segurança de tipos
T_Channel = TypeVar("T_Channel", bound=BaseChannelConfig)


class ChannelsFileSchema(TypedDict, Generic[T_Channel]):
    """Contrato estrito para a raiz do channels.json."""

    channels: List[T_Channel]
