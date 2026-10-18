"""Gravação dos arquivos de Terapias na pasta do iCloud.

Estrutura: <iCloud>/Terapias/<Ano_Mes>/NotaFiscal_<Ano_Mes>_<Terapeuta>.pdf
           <iCloud>/Terapias/<Ano_Mes>/Comprovante_<Ano_Mes>_<Terapeuta>.png
"""
import re
from pathlib import Path

ICLOUD_ROOT = Path.home() / "Library" / "Mobile Documents" / "com~apple~CloudDocs"
PASTA_TERAPIAS = "Terapias"
RE_ANO_MES = re.compile(r"^\d{4}_\d{2}$")
RE_NOME_ARQ = re.compile(r"^(NotaFiscal|Comprovante)_\d{4}_\d{2}_[^/\\:*?\"<>|]+\.(pdf|png)$")


def nome_terapeuta(texto: str) -> str:
    """Remove caracteres inválidos e espaços: 'Aloma Silva' -> 'AlomaSilva'."""
    limpo = re.sub(r"[^\w]+", "", texto, flags=re.UNICODE)
    if not limpo:
        raise ValueError("nome da terapeuta vazio")
    return limpo


def nome_arquivo(tipo: str, ano_mes: str, terapeuta: str) -> str:
    """tipo: 'nota' ou 'comprovante'. Retorna o nome final."""
    if tipo == "nota":
        return f"NotaFiscal_{ano_mes}_{nome_terapeuta(terapeuta)}.pdf"
    if tipo == "comprovante":
        return f"Comprovante_{ano_mes}_{nome_terapeuta(terapeuta)}.png"
    raise ValueError(f"tipo desconhecido: {tipo}")


def salvar(raiz: Path, ano_mes: str, nome: str, dados: bytes) -> Path:
    """Grava em <raiz>/Terapias/<ano_mes>/<nome>. Não sobrescreve: acrescenta (2), (3)…"""
    if not RE_ANO_MES.match(ano_mes):
        raise ValueError("mês inválido, use AAAA_MM")
    if not RE_NOME_ARQ.match(nome):
        raise ValueError("nome de arquivo inválido")
    pasta = Path(raiz) / PASTA_TERAPIAS / ano_mes
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / nome
    n = 2
    while destino.exists():
        destino = pasta / f"{Path(nome).stem} ({n}){Path(nome).suffix}"
        n += 1
    destino.write_bytes(dados)
    return destino
