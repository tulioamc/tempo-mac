"""Tempo para Mac: abre o site do Tempo numa janela própria e ganha
funções nativas (gravar no iCloud) pela ponte js_api do pywebview."""
import base64
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


def main():
    janela = webview.create_window(
        "Tempo", SITE, js_api=Api(), width=1280, height=860, min_size=(900, 640),
    )
    # Ociosidade do Mac -> sugestões de pausa no site (window.TempoBridge.reportIdle)
    webview.start(monitorar, janela, private_mode=False)


if __name__ == "__main__":
    main()
