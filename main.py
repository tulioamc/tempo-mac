"""Tempo para Mac: abre o site do Tempo numa janela própria e ganha
funções nativas (gravar no iCloud) pela ponte js_api do pywebview."""
import base64
import subprocess
from pathlib import Path

import webview

from icloud import ICLOUD_ROOT, nome_arquivo, salvar
from idle import monitorar

SITE = "https://apptempo-abon.vercel.app"


class Api:
    def icloud_disponivel(self) -> bool:
        return ICLOUD_ROOT.exists()

    def salvar_terapia(self, tipo: str, ano_mes: str, terapeuta: str, base64_dados: str) -> str:
        """Grava nota fiscal (PDF) ou comprovante (PNG) em iCloud/Terapias/<ano_mes>. Retorna o caminho."""
        if not ICLOUD_ROOT.exists():
            raise RuntimeError("iCloud Drive não encontrado neste Mac")
        nome = nome_arquivo(tipo, ano_mes, terapeuta)
        dados = base64.b64decode(base64_dados)
        destino: Path = salvar(ICLOUD_ROOT, ano_mes, nome, dados)
        return str(destino)

    def criar_lembrete(self, titulo: str, quando: str) -> bool:
        """Cria um lembrete com alarme no app Lembretes (lista 'Tempo'); sincroniza com o iPhone.
        quando: 'AAAA-MM-DDTHH:MM' (hora local). Lança erro se o macOS negar a permissão."""
        ano, mes, dia = (int(x) for x in quando.split("T")[0].split("-"))
        hh, mm = (int(x) for x in quando.split("T")[1][:5].split(":"))
        t = titulo.replace("\\", "\\\\").replace('"', '\\"')
        script = (
            'tell application "Reminders"\n'
            '  if not (exists list "Tempo") then make new list with properties {name:"Tempo"}\n'
            '  set d to current date\n'
            '  set day of d to 1\n'
            f"  set year of d to {ano}\n"
            f"  set month of d to {mes}\n"
            f"  set day of d to {dia}\n"
            f"  set hours of d to {hh}\n"
            f"  set minutes of d to {mm}\n"
            "  set seconds of d to 0\n"
            f'  tell list "Tempo" to make new reminder with properties {{name:"{t}", remind me date:d}}\n'
            "end tell"
        )
        subprocess.run(["osascript", "-e", script], check=True, capture_output=True, timeout=30)
        return True


def main():
    janela = webview.create_window(
        "Tempo", SITE, js_api=Api(), width=1280, height=860, min_size=(900, 640),
    )
    # Ociosidade do Mac -> sugestões de pausa no site (window.TempoBridge.reportIdle)
    webview.start(monitorar, janela, private_mode=False)


if __name__ == "__main__":
    main()
