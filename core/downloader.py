"""
core/downloader.py

Módulo responsável por gerenciar a execução segura de subprocessos (como o yt-dlp),
controlando o diretório de trabalho (working directory), o tratamento de erros
e a exibição de logs em tempo real no console.
"""

import subprocess
import sys
from pathlib import Path
from typing import List


class MediaDownloader:
    """
    Gerenciador centralizado para execução de comandos externos de download.
    """

    @staticmethod
    def execute(command: List[str], output_dir: Path) -> bool:
        """
        Executa um comando CLI (ex: yt-dlp) em um diretório de destino específico,
        redirecionando a saída padrão para o console em tempo real.

        Args:
            command (List[str]): Lista de argumentos do comando a ser executado.
            output_dir (Path): Pasta física onde o comando deve ser executado (working directory).

        Returns:
            bool: True se o download/execução ocorreu com sucesso (exit code 0), False caso contrário.
        """

        # Garante que a pasta física do canal existe antes de rodar o comando
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n[DOWNLOADER] Executando em: {output_dir.resolve()}")
        print(f"[DOWNLOADER] Comando: {' '.join(command)}")

        try:
            result = subprocess.run(command, cwd=str(output_dir), text=True, encoding="utf-8", errors="replace")

            if result.returncode == 0:
                print(f"[DOWNLOADER] [SUCESSO] Processo finalizado com êxito.")
                return True
            else:
                print(f"[DOWNLOADER] [AVISO] Processo finalizado com código de erro: {result.returncode}")
                return False

        except FileNotFoundError:
            print(
                f"[DOWNLOADER] [ERRO CRÍTICO] O executável '{command[0]}' não foi encontrado no PATH do sistema.",
                file=sys.stderr,
            )
            return False

        except Exception as e:
            print(f"[DOWNLOADER] [ERRO CRÍTICO] Falha inesperada ao executar o subprocesso: {e}", file=sys.stderr)
            return False
