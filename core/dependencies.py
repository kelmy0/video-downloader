"""
core/dependencies.py

Módulo responsável por verificar a integridade e a presença das
dependências externas (yt-dlp e ffmpeg) no sistema.
"""

import shutil
from pathlib import Path
from typing import Optional


class DependencyChecker:
    """Verificador de dependências de sistema necessárias para o arquivamento."""

    @staticmethod
    def check_bin(bin_name: str) -> Optional[Path]:
        """
        Verifica se um executável está disponível no PATH do sistema.
        Retorna o caminho absoluto do binário se encontrado, ou None caso contrário.
        """
        path = shutil.which(bin_name)
        return Path(path) if path else None

    @classmethod
    def validate_enviroment(cls) -> bool:
        """
        Valida se todas as ferramentas essenciais estão instaladas.
        """
        print(f"\033[36m[INFO]\033[0m Verificando dependências do sistema...")

        yt_dlp_path = cls.check_bin("yt-dlp")
        ffmpeg_path = cls.check_bin("ffmpeg")

        all_ok = True

        if not yt_dlp_path:
            print(f"\033[31m[FALHA]\033[0m O executável 'yt-dlp' não foi encontrado no PATH do sistema.")
            all_ok = False

        if not ffmpeg_path:
            print(f"\033[33m[FALHA]\033[0m O 'ffmpeg' não foi encontrado.")
            all_ok = False

        if not all_ok:
            return all_ok

        print(f"\033[32m[OK]\033[0m yt-dlp encontrado em: {yt_dlp_path}")
        print(f"\033[32m[OK]\033[0m ffmpeg encontrado em: {ffmpeg_path}")

        return all_ok
