"""Ociosidade e app em primeiro plano no Mac, para as sugestões de pausa do Tempo.

O site recebe (via window.TempoBridge.reportIdle) o intervalo em que o Mac ficou
parado, com o app que estava em uso. Nada é aplicado sozinho: vira sugestão no site.
"""
import json
import re
import subprocess
import threading
import time
from datetime import datetime, timezone

LIMITE_PADRAO_S = 300  # 5 min, igual ao padrão do site
RE_HID_IDLE = re.compile(r'"HIDIdleTime"\s*=\s*(\d+)')
APPS_PAUSA_POS = {"WhatsApp"}  # o uso desses apps vira aviso de pausa, depois do fato


def parse_hid_idle(saida_ioreg: str) -> float | None:
    """Lê HIDIdleTime (nanossegundos) da saída de `ioreg -c IOHIDSystem`. Retorna segundos."""
    m = RE_HID_IDLE.search(saida_ioreg)
    return int(m.group(1)) / 1e9 if m else None


def ocioso_segundos() -> float | None:
    try:
        saida = subprocess.run(["ioreg", "-c", "IOHIDSystem"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_hid_idle(saida)


def parse_tela_bloqueada(saida_ioreg: str) -> bool:
    """Lê CGSSessionScreenIsLocked da saída de `ioreg -n Root -d1`."""
    return re.search(r'"CGSSessionScreenIsLocked"\s*=\s*Yes', saida_ioreg) is not None


def tela_bloqueada() -> bool | None:
    try:
        saida = subprocess.run(["ioreg", "-n", "Root", "-d1"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return parse_tela_bloqueada(saida)


def app_em_primeiro_plano() -> str | None:
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return None
    nome = r.stdout.strip()
    return nome or None


class Detector:
    """Máquina de estados: quando fica ocioso por `limite_s` e depois volta a usar, devolve o intervalo."""

    def __init__(self, limite_s: float = LIMITE_PADRAO_S):
        self.limite = limite_s
        self.inicio = None   # instante (s) em que a ociosidade começou
        self.app = None      # app em uso quando ficou ocioso
        self.ultimo = 0.0    # última leitura de ociosidade

    def passo(self, agora: float, ocioso_s: float, app: str | None):
        """Retorna (inicio, fim, app) quando o uso volta depois de uma ociosidade longa; senão None."""
        if self.inicio is None:
            if ocioso_s >= self.limite:
                self.inicio = agora - ocioso_s
                self.app = app
            self.ultimo = ocioso_s
            return None
        if ocioso_s < self.ultimo:  # houve entrada: o uso voltou
            fim = agora - ocioso_s
            resultado = (self.inicio, fim, self.app)
            self.inicio, self.app, self.ultimo = None, None, ocioso_s
            return resultado
        self.ultimo = ocioso_s
        return None


class Trecho:
    """Uso de um app de pausa (ex.: WhatsApp): devolve (inicio, fim, app) quando o uso sai dele."""

    def __init__(self, alvo=APPS_PAUSA_POS):
        self.alvo = alvo
        self.inicio = None
        self.ultimo = None
        self.app = None

    def passo(self, agora: float, app: str | None):
        if app in self.alvo:
            if self.inicio is None:
                self.inicio, self.app = agora, app
            self.ultimo = agora
            return None
        if self.inicio is not None:
            resultado = (self.inicio, self.ultimo, self.app)
            self.inicio = self.ultimo = self.app = None
            return resultado
        return None


def iso(t: float) -> str:
    return datetime.fromtimestamp(t, timezone.utc).isoformat().replace("+00:00", "Z")


def monitorar(janela, intervalo_s: float = 10, limite_s: float = LIMITE_PADRAO_S):
    """Laço em segundo plano: envia cada pausa detectada ao site aberto na janela."""
    det = Detector(limite_s)
    trecho = Trecho()
    ultimo_app = None

    def enviar(inicio, fim, app):
        js = (f"window.TempoBridge && window.TempoBridge.reportIdle("
              f"{json.dumps(iso(inicio))}, {json.dumps(iso(fim))}, {json.dumps(app)})")
        try:
            janela.evaluate_js(js)
        except Exception:
            pass  # página ainda não carregou ou a janela foi fechada (ver README)

    def laco():
        nonlocal ultimo_app
        while True:
            agora = time.time()
            bloqueada = tela_bloqueada() is True
            ocioso = ocioso_segundos()
            if bloqueada:
                ocioso = max(ocioso or 0, limite_s)  # tela bloqueada conta como parada
            if ocioso is not None:
                if ocioso < limite_s and not bloqueada:
                    ultimo_app = app_em_primeiro_plano() or ultimo_app
                resultado = det.passo(agora, ocioso, ultimo_app)
                if resultado:
                    enviar(*resultado)
                # WhatsApp (ou outro app de pausa) em primeiro plano: aviso depois do fato
                app_trecho = None if (bloqueada or ocioso >= limite_s) else ultimo_app
                resultado = trecho.passo(agora, app_trecho)
                if resultado:
                    enviar(*resultado)
            time.sleep(intervalo_s)

    threading.Thread(target=laco, daemon=True).start()
