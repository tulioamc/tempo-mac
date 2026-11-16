"""Atualização automática do app do Mac.

O app compara a própria versão (Info.plist) com a da pasta ~/tempo-build (arquivo VERSION).
Se a pasta tem versão diferente, roda atualizar.sh em segundo plano: ao abrir o app, ou
quando você está parado há 5 minutos ou com a tela bloqueada. O site também recebe o aviso
(window.TempoBridge.macUpdate) e mostra o botão "Atualizar app do Mac" para fazer na hora.
"""
from __future__ import annotations

import json
import plistlib
import subprocess
import sys
import threading
import time
from pathlib import Path

from idle import ocioso_segundos, tela_bloqueada

PASTA = Path.home() / "tempo-build"
SCRIPT = PASTA / "atualizar.sh"
OCIOSO_MIN_S = 300


def versao_instalada() -> str | None:
    try:
        info = Path(sys.executable).resolve().parents[1] / "Info.plist"
        return plistlib.loads(info.read_bytes()).get("CFBundleShortVersionString")
    except Exception:
        return None


def versao_disponivel() -> str | None:
    try:
        return (PASTA / "VERSION").read_text(encoding="utf-8").strip() or None
    except Exception:
        return None


def falhou(versao: str) -> bool:
    """A última tentativa dessa mesma versão deu erro: espera a pasta mudar antes de tentar de novo."""
    try:
        return (PASTA / ".atualizar_falhou").read_text(encoding="utf-8").strip() == versao
    except Exception:
        return False


def pendente() -> str | None:
    """Versão nova esperando para ser instalada (ou None)."""
    if not getattr(sys, "frozen", False):
        return None  # rodando pelo código (desenvolvimento): não se atualiza
    nova, atual = versao_disponivel(), versao_instalada()
    if not nova or not atual or nova == atual or falhou(nova) or not SCRIPT.exists():
        return None
    return nova


def atualizar_agora() -> bool:
    """Roda o atualizador fora deste processo (ele fecha e reabre o app)."""
    if not SCRIPT.exists():
        return False
    subprocess.Popen(["/bin/bash", str(SCRIPT)], cwd=str(PASTA), start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return True


def monitorar_atualizacao(janela, intervalo_s: float = 300):
    inicio = time.time()

    def laco():
        time.sleep(20)  # deixa o site carregar
        while True:
            nova = pendente()
            if nova:
                try:
                    janela.evaluate_js(f"window.TempoBridge && window.TempoBridge.macUpdate && window.TempoBridge.macUpdate({json.dumps(nova)})")
                except Exception:
                    pass
                parado = (ocioso_segundos() or 0) >= OCIOSO_MIN_S or bool(tela_bloqueada())
                if time.time() - inicio < 90 or parado:
                    atualizar_agora()
                    return
            time.sleep(intervalo_s)

    threading.Thread(target=laco, daemon=True).start()
