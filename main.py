"""Tempo para Mac: abre o site do Tempo numa janela própria e ganha
funções nativas (gravar no iCloud) pela ponte js_api do pywebview."""
import base64
import json
import subprocess
from datetime import datetime
from pathlib import Path

import webview

from icloud import ICLOUD_ROOT, nome_arquivo, salvar
from idle import monitorar

SITE = "https://apptempo-abon-git-chatgpt-v202122-tulio22.vercel.app"
FEEDBACK = Path.home() / "Documents" / "APPTEMPO-feedback"
TITULO_PX = 28  # altura da barra de título da janela, em pontos (ajustar se o print vier deslocado)


class Api:
    def __init__(self):
        self.janela = None
        self._pendentes = {}

    def capturar_feedback(self, rect: dict) -> str:
        """Print da área marcada no site (x, y, w, h em pontos dentro da janela).
        Grava o PNG já com a marcação, antes da caixa de comentário aparecer. Retorna o identificador."""
        if self.janela is None:
            raise RuntimeError("Janela ainda não está pronta")
        FEEDBACK.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        png = str(FEEDBACK / f"{stamp}.png")
        if rect.get("tela"):
            # clique: tela toda (o círculo já está desenhado no site)
            subprocess.run(["screencapture", "-x", png], check=True, capture_output=True, timeout=20)
            area = None
        else:
            x = int(self.janela.x + rect["x"])
            y = int(self.janela.y + TITULO_PX + rect["y"])
            w, h = max(1, int(rect["w"])), max(1, int(rect["h"]))
            subprocess.run(["screencapture", "-x", f"-R{x},{y},{w},{h}", png], check=True, capture_output=True, timeout=20)
            area = [x, y, w, h]
        self._pendentes[stamp] = {"pagina": rect.get("pagina", ""), "versao": rect.get("versao", ""), "tela": bool(rect.get("tela")), "area": area}
        return stamp

    def salvar_feedback(self, identificador: str, comentario: str) -> str:
        """Grava o comentário (TXT) ao lado do print. Retorna o caminho do TXT."""
        meta = self._pendentes.pop(identificador, None)
        if meta is None:
            raise RuntimeError("Print não encontrado")
        txt = FEEDBACK / f"{identificador}.txt"
        conteudo = {"data": identificador, "comentario": comentario, "print": f"{identificador}.png", **meta}
        txt.write_text(json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(txt)

    def descartar_feedback(self, identificador: str) -> bool:
        """Cancelado: apaga o print pendente."""
        self._pendentes.pop(identificador, None)
        (FEEDBACK / f"{identificador}.png").unlink(missing_ok=True)
        return True

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
    api = Api()
    janela = webview.create_window(
        "Tempo", SITE, js_api=api, width=1280, height=860, min_size=(900, 640),
    )
    api.janela = janela
    # Ociosidade do Mac -> sugestões de pausa no site (window.TempoBridge.reportIdle)
    webview.start(monitorar, janela, private_mode=False)


if __name__ == "__main__":
    main()
