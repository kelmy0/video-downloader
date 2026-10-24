"""
core/downloader.py

Módulo responsável por gerenciar a execução segura do yt_dlp,
controlando o diretório de trabalho (working directory), o tratamento de erros
e a exibição de logs em tempo real no console.
"""

import yt_dlp
import sys
from pathlib import Path
from typing import Dict


class MediaDownloader:
    """
    Gerenciador centralizado para execução de comandos externos de download.
    """

    @staticmethod
    def execute(ydl_opts: Dict[str, object], output_dir: Path) -> bool:
        """
        Executa o download utilizando diretamente a API Python do yt-dlp,
        redirecionando os logs e colorindo a saída no terminal.

        Args:
            ydl_opts (Dict[str, object]): Dicionário de opções gerado pelo extrator.
            output_dir (Path): Pasta física de destino.

        Returns:
            bool: True se o download ocorreu com sucesso, False caso contrário.
        """

        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n\033[34m[DOWNLOADER]\033[0m Executando em: \033[1m{output_dir.resolve()}\033[0m")

        item_url = str(ydl_opts.pop("url_alvo", ""))
        if not item_url:
            print(
                f"\033[31m[DOWNLOADER] [ERRO CRÍTICO]\033[0m Nenhuma URL alvo foi fornecida nas opções do yt-dlp.",
                file=sys.stderr,
            )
            return False

        print(f"\n\033[34m[DOWNLOADER]\033[0m Iniciando motor yt-dlp para a URL: \033[36m{item_url}\033[0m")

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                ydl.download([item_url])

            print(f"\033[32m[DOWNLOADER] [SUCESSO]\033[0m Processo finalizado com êxito.")
            return True

        except Exception as e:
            print(
                f"\033[31m[DOWNLOADER] [ERRO CRÍTICO]\033[0m Falha ao executar o download via yt-dlp: {e}",
                file=sys.stderr,
            )
            return False
