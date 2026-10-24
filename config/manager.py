"""
config/manager.py

Módulo responsável por gerenciar o carregamento das configurações globais,
dos canais cadastrados, validação de cooldown e persistência do estado,
utilizando tipagem estrita via TypedDict.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Tuple
from schemas.config_schema import AppConfig
from schemas.channel_schema import BaseChannelConfig


class ConfigManager:
    """Gerenciador centralizado das configurações e estado dos canais."""

    def __init__(self):
        self.diretorio_base: Path = Path.cwd()
        self.config_dir: Path = self.diretorio_base / "config"
        self.config_path: Path = self.config_dir / "config.json"
        self.channels_path: Path = self.config_dir / "channels.json"

    def carregar_configuracoes(self) -> Tuple[Optional[Path], int, Optional[Path]]:
        """
        1. Valida e carrega o config.json (diretório raiz, cooldown e cookies opcionais).
        """
        print(f"\033[34m[INFO]\033[0m Diretório base do sistema: {self.diretorio_base}")

        # 1. Valida se o arquivo de configuração existe
        if not self.config_path.exists():
            print(f"[ERRO CRÍTICO] Arquivo de configuração não encontrado em: {self.config_path}")
            return None, 0, None

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                app_config: AppConfig = json.load(f)

            raw_download_path: str = ""
            raw_cookies_path: str = ""

            if "path" in app_config:
                path_config = app_config["path"]
                raw_download_path = path_config.get("download_path", "")
                raw_cookies_path = path_config.get("cookies_path", "")

            cooldown_minutes: int = app_config.get("cooldown_minutes", 0)

            if not raw_download_path:
                print(f"[ERRO CRÍTICO] O parâmetro 'path.download_path' não foi definido no config.json.")
                return None, 0, None

            root_download_dir = Path(raw_download_path)

            cookies_path: Optional[Path] = None
            if raw_cookies_path:
                potential_path = Path(raw_cookies_path)

                if potential_path.is_dir() or not potential_path.name.endswith(".txt"):
                    potential_path = potential_path / "cookies.txt"

                if potential_path.exists():
                    cookies_path = potential_path
                    print(f"\033[34m[INFO]\033[0m Arquivo de cookies carregado com sucesso: {cookies_path}")
                else:
                    print(
                        f"\033[33m[AVISO]\033[0m O caminho de cookies informado não foi encontrado ou é inválido: {potential_path}"
                    )
                    print(f"\033[33m[AVISO]\033[0m O sistema continuará a execução sem autenticação de cookies.")
            else:
                print(f"\033[34m[INFO]\033[0m Nenhum caminho de cookies configurado. Executando em modo público.")

        except Exception as e:
            print(f"\033[31m[ERRO CRÍTICO]\033[0m Falha ao ler o config.json: {e}")
            return None, 0, None

        print(f"\033[34m[INFO]\033[0m Diretório raiz de downloads: {root_download_dir.resolve()}")

        return root_download_dir, cooldown_minutes, cookies_path

    def carregar_canais(self) -> List[BaseChannelConfig]:
        """
        Carrega a lista genérica de canais que estendem o BaseChannelConfig.
        """
        if not self.channels_path.exists():
            print(f"\033[31m[ERRO CRÍTICO]\033[0m Arquivo channels.json não encontrado em: {self.channels_path}")
            return []

        try:
            with open(self.channels_path, "r", encoding="utf-8") as f:
                channels_data = json.load(f)
        except Exception as e:
            print(f"\033[31m[ERRO CRÍTICO]\033[0m Falha ao ler o arquivo channels.json: {e}")
            return []

        channels: List[BaseChannelConfig] = channels_data.get("channels", [])
        if not channels:
            print("\033[34m[INFO]\033[0m Nenhum canal configurado no arquivo channels.json.")
            return []

        return channels

    def verificar_cooldown(self, channel_config: BaseChannelConfig, cooldown_minutes: int, agora: datetime) -> bool:
        """
        Verifica se o canal está no período de cooldown. Retorna True se deve PULAR o canal.
        """
        last_checked_str: Optional[str] = channel_config.get("last_checked")
        name: str = channel_config.get("name", "Canal")

        if cooldown_minutes > 0 and last_checked_str:
            try:
                ultima_consulta = datetime.strptime(last_checked_str, "%Y-%m-%d %H:%M:%S")
                tempo_decorrido = agora - ultima_consulta
                limite_cooldown = timedelta(minutes=cooldown_minutes)

                if tempo_decorrido < limite_cooldown:
                    tempo_restante = limite_cooldown - tempo_decorrido
                    minutos_restantes = int(tempo_restante.total_seconds() // 60)
                    segundos_restantes = int(tempo_restante.total_seconds() % 60)
                    print(
                        f"[COOLDOWN] Canal '{name}' ignorado. Em período de espera ({minutos_restantes}m {segundos_restantes}s restantes)."
                    )
                    return True
            except ValueError:
                pass

        return False

    def salvar_alteracoes_canais(self, channels: List[BaseChannelConfig]) -> None:
        """
        Salva o estado atualizado de volta no channels.json.
        """

        try:
            channels_data = {"channels": channels}
            with open(self.channels_path, "w", encoding="utf-8") as f:
                json.dump(channels_data, f, indent=4, ensure_ascii=False)
                print(f"\n[MEMÓRIA] Estado de 'last_checked' atualizado com sucesso no channels.json.")

        except Exception as e:
            print(f"\n[AVISO] Falha ao atualizar o arquivo channels.json: {e}")
