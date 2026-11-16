"""Mensagens que você mandou no WhatsApp Desktop, por contato e por dia.

Lê só o nome da conversa, o tipo (contato, grupo ou status), a data e se a
mensagem foi sua (ZISFROMME). O texto das mensagens nunca é lido.
Também lê o texto de PDFs de notas fiscais enviados nas conversas de terapia
(lista NOTAS_CONTATOS). Os arquivos são lidos; as mensagens não.
Envia ao site (window.TempoBridge.reportWhatsApp) a cada 5 min. Precisa de
Acesso Total ao Disco para o Tempo (Ajustes do Sistema > Privacidade e Segurança).
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

BANCO = Path.home() / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/ChatStorage.sqlite"
EPOCA_CORE_DATA = 978307200  # 2001-01-01 em segundos Unix
INTERVALO_S = 300
TIPO_STATUS = 3  # status/broadcast: não é conversa
MIDIA = Path.home() / "Library/Group Containers/group.net.whatsapp.WhatsApp.shared/Message"
# Conversas cujas notas em PDF vão para a tabela de reembolsos (nome igual ao do WhatsApp).
NOTAS_CONTATOS = {  # conversa do WhatsApp -> nome da linha na tabela de reembolsos
    "Carol AT": "AT",
    "Dra Raquel Barreto Psicopedagoga": "Raquel",
    "Aloma Consultório": "Aloma",
    "Erika Gomes (Clau/Aconchego)": "Claudiane",
    "Homero Futebol/ Bicicleta/ Skate": "Homero",
    "ARGOS FINANCEIRO HUGO VIANA": "Patrícia",
}

SQL = """
select s.ZCONTACTJID, s.ZPARTNERNAME, s.ZSESSIONTYPE,
       date(m.ZMESSAGEDATE + ?, 'unixepoch', 'localtime') as dia,
       count(*) as enviadas
from ZWAMESSAGE m join ZWACHATSESSION s on m.ZCHATSESSION = s.Z_PK
where m.ZISFROMME = 1 and s.ZSESSIONTYPE != ?
  and m.ZMESSAGEDATE + ? between ? and ?
group by s.ZCONTACTJID, dia
"""


def ler_contagens(banco=BANCO, desde=None, ate=None) -> list[dict]:
    """Conta mensagens enviadas por conversa e dia, entre `desde` e `ate` (timestamps Unix)."""
    con = sqlite3.connect(f"file:{banco}?mode=ro", uri=True)
    try:
        linhas = con.execute(SQL, (EPOCA_CORE_DATA, TIPO_STATUS, EPOCA_CORE_DATA, desde, ate)).fetchall()
    finally:
        con.close()
    return [
        {"jid": jid, "name": nome or jid, "grupo": tipo == 1, "dia": dia, "enviadas": n}
        for jid, nome, tipo, dia, n in linhas if jid
    ]


SQL_MIDIA = """
select s.ZPARTNERNAME, mi.ZMEDIALOCALPATH, m.ZMESSAGEDATE
from ZWAMESSAGE m join ZWACHATSESSION s on m.ZCHATSESSION = s.Z_PK
join ZWAMEDIAITEM mi on m.ZMEDIAITEM = mi.Z_PK
where (mi.ZMEDIALOCALPATH like '%.pdf' or mi.ZMEDIALOCALPATH like '%.png'
       or mi.ZMEDIALOCALPATH like '%.jpg' or mi.ZMEDIALOCALPATH like '%.jpeg')
  and m.ZMESSAGEDATE + ? >= ?
order by m.ZMESSAGEDATE
"""
REGISTRO = Path.home() / "Library/Application Support/Tempo/wa_notas_v2.json"  # arquivos lidos (sha256) e fila de envio


def janela_mes(data: datetime) -> str:
    """Notas de 20 do mês anterior a 19 do mês atual entram no mês atual; a partir do dia 20, no seguinte."""
    ano, mes = data.year, data.month
    if data.day >= 20:
        mes += 1
        if mes == 13:
            ano, mes = ano + 1, 1
    return f"{ano:04d}-{mes:02d}"


def _carregar_registro() -> dict:
    try:
        return json.loads(REGISTRO.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _salvar_registro(reg: dict) -> None:
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(json.dumps(reg), encoding="utf-8")


def _ocr_imagem(caminho: Path) -> str | None:
    """Reconhecimento de texto do macOS (ocrmac). Roda no Mac; o documento não sai do aparelho."""
    try:
        from ocrmac import ocrmac
    except ImportError:
        return None
    resultado = ocrmac.OCR(str(caminho), language_preference=["pt-BR"]).recognize()
    return "\n".join(t for t, _conf, _box in resultado)


def _texto_do_arquivo(caminho: Path, dados: bytes) -> str | None:
    """PDF com texto: texto nativo. PDF escaneado: primeira página vira PNG (sips do macOS) e vai para OCR.
    Foto (PNG/JPG): OCR direto."""
    import io
    import subprocess
    tmp = REGISTRO.parent / "ocr_tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    if caminho.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        texto = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(dados)).pages).strip()
        if texto:
            return texto
        origem = tmp / "pagina.pdf"
        origem.write_bytes(dados)
        destino = tmp / "pagina.png"
        try:
            subprocess.run(["/usr/bin/sips", "-s", "format", "png", str(origem), "--out", str(destino)],
                           check=True, capture_output=True, timeout=60)
            return _ocr_imagem(destino)
        finally:
            origem.unlink(missing_ok=True)
            destino.unlink(missing_ok=True)
    arquivo = tmp / ("imagem" + caminho.suffix.lower())
    arquivo.write_bytes(dados)
    try:
        return _ocr_imagem(arquivo)
    finally:
        arquivo.unlink(missing_ok=True)


def _tipo_do_documento(texto: str) -> str | None:
    if re.search(r"CHAVE DE ACESSO DA NFS-e|NFS-e", texto, re.I):
        return "nota"
    if "R$" in texto and re.search(r"pix|comprovante|transfer", texto, re.I):
        return "comprovante"
    return None


def _ja_salvo(pasta: Path, nome: str, sha: str) -> Path | None:
    """Mesmo arquivo já está na pasta do mês (de uma leitura anterior)? Evita cópias "(2)"."""
    if not pasta.exists():
        return None
    base, ext = Path(nome).stem, Path(nome).suffix
    for c in pasta.glob(f"{base}*{ext}"):
        try:
            if hashlib.sha256(c.read_bytes()).hexdigest() == sha:
                return c
        except OSError:
            pass
    return None


def ler_notas(banco=BANCO, desde=None) -> None:
    """Procura notas (PDF/foto) e comprovantes (PNG/JPG) novos nas conversas de NOTAS_CONTATOS.
    Cada arquivo é lido uma vez: guarda uma cópia no iCloud (Terapias/Ano_Mes) e deixa o item
    na fila do registro até o site confirmar o recebimento. Nunca lê o texto das mensagens."""
    from icloud import ICLOUD_ROOT, PASTA_TERAPIAS, nome_arquivo, salvar
    con = sqlite3.connect(f"file:{banco}?mode=ro", uri=True)
    try:
        linhas = con.execute(SQL_MIDIA, (EPOCA_CORE_DATA, desde or 0)).fetchall()
    finally:
        con.close()
    reg = _carregar_registro()
    mudou = False
    for nome, caminho, unix in linhas:
        linha = NOTAS_CONTATOS.get(nome)
        if not linha or not caminho:
            continue
        arquivo = next((c for c in (MIDIA / caminho, MIDIA.parent / caminho) if c.exists()), None)
        if arquivo is None:
            continue  # apagado ou ainda não baixado
        try:
            dados = arquivo.read_bytes()
        except OSError:
            continue
        sha = hashlib.sha256(dados).hexdigest()
        if sha in reg:
            continue
        try:
            texto = _texto_do_arquivo(arquivo, dados)
        except Exception:
            continue  # falha passageira de leitura: tenta de novo na próxima volta
        if texto is None:
            continue  # reconhecimento de texto indisponível: tenta de novo depois
        tipo = _tipo_do_documento(texto)
        if not tipo:
            reg[sha] = {"enviado": True}  # foto ou PDF que não é nota nem comprovante: não lê de novo
            mudou = True
            continue
        data = datetime.fromtimestamp(unix + EPOCA_CORE_DATA)
        ano_mes = janela_mes(data).replace("-", "_")
        salvo = None
        ext_ok = (tipo == "nota" and arquivo.suffix.lower() == ".pdf") or (tipo == "comprovante" and arquivo.suffix.lower() == ".png")
        if ext_ok and ICLOUD_ROOT.exists():
            try:
                nome_final = nome_arquivo(tipo, ano_mes, linha)
                existente = _ja_salvo(ICLOUD_ROOT / PASTA_TERAPIAS / ano_mes, nome_final, sha)
                salvo = str(existente or salvar(ICLOUD_ROOT, ano_mes, nome_final, dados))
            except Exception as e:
                print(f"WhatsApp: não salvou no iCloud ({e})", file=sys.stderr)
        reg[sha] = {"enviado": False, "item": {"id": sha, "contato": nome, "tipo": tipo, "texto": texto,
                                               "data": data.date().isoformat(), "arquivo": salvo}}
        mudou = True
    if mudou:
        _salvar_registro(reg)


def notas_pendentes() -> list[dict]:
    """Itens lidos que o site ainda não confirmou."""
    return [v["item"] for v in _carregar_registro().values() if isinstance(v, dict) and not v.get("enviado") and v.get("item")]


def marcar_enviadas(ids) -> None:
    """O site confirmou estes itens: saem da fila (o texto do documento é apagado do registro)."""
    reg = _carregar_registro()
    for i in ids or []:
        if i in reg:
            reg[i] = {"enviado": True}
    _salvar_registro(reg)


def monitorar_whatsapp(janela, intervalo_s: float = INTERVALO_S):
    """Laço em segundo plano: manda ao site a contagem de hoje e de ontem."""
    avisado = False

    def enviar():
        nonlocal avisado
        agora = datetime.now()
        inicio = datetime.combine((agora - timedelta(days=1)).date(), datetime.min.time())
        try:
            linhas = ler_contagens(BANCO, inicio.timestamp(), agora.timestamp())
        except Exception as e:  # sem Acesso Total ao Disco ou sem o WhatsApp instalado
            if not avisado:
                print(f"WhatsApp: não foi possível ler o banco ({e}). Ative Acesso Total ao Disco para o Tempo.", file=sys.stderr)
                avisado = True
            return
        js = f"window.TempoBridge && window.TempoBridge.reportWhatsApp({json.dumps(linhas, ensure_ascii=False)})"
        try:
            janela.evaluate_js(js)
        except Exception:
            pass  # página ainda não carregou ou a janela foi fechada
        # notas e comprovantes: ficam na fila até o site (já com os dados carregados) confirmar o recebimento
        try:
            ler_notas(BANCO, (agora - timedelta(days=60)).timestamp())
            pend = notas_pendentes()
            if pend:
                js = ("(window.TempoBridge && window.TempoBridge.reportNfse) ? JSON.stringify(window.TempoBridge.reportNfse("
                      + json.dumps(pend, ensure_ascii=False) + ")) : '[]'")
                res = janela.evaluate_js(js)
                ids = json.loads(res) if isinstance(res, str) else (res or [])
                marcar_enviadas(ids)
        except Exception as e:
            print(f"WhatsApp notas: {e}", file=sys.stderr)

    def laco():
        while True:
            enviar()
            # enquanto o site não confirmou tudo (página ainda carregando), tenta de novo em 30 s
            try:
                falta = bool(notas_pendentes())
            except Exception:
                falta = False
            time.sleep(30 if falta else intervalo_s)

    threading.Thread(target=laco, daemon=True).start()
