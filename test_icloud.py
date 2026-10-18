import tempfile
from pathlib import Path
from icloud import nome_arquivo, salvar, nome_terapeuta

assert nome_terapeuta("Aloma Silva") == "AlomaSilva"
assert nome_arquivo("nota", "2026_10", "Raquel Souza") == "NotaFiscal_2026_10_RaquelSouza.pdf"
assert nome_arquivo("comprovante", "2026_10", "Patricia") == "Comprovante_2026_10_Patricia.png"
try:
    nome_arquivo("x", "2026_10", "A"); raise SystemExit("falhou: tipo inválido")
except ValueError: pass
with tempfile.TemporaryDirectory() as d:
    raiz = Path(d)
    p1 = salvar(raiz, "2026_10", "NotaFiscal_2026_10_Raquel.pdf", b"a")
    p2 = salvar(raiz, "2026_10", "NotaFiscal_2026_10_Raquel.pdf", b"b")
    assert p1.name == "NotaFiscal_2026_10_Raquel.pdf" and p2.name == "NotaFiscal_2026_10_Raquel (2).pdf"
    assert p1.parent == raiz / "Terapias" / "2026_10"
    for ruim in [("2026-10", "NotaFiscal_2026_10_A.pdf"), ("2026_10", "../x.pdf"), ("2026_10", "foto.jpg")]:
        try:
            salvar(raiz, ruim[0], ruim[1], b""); raise SystemExit(f"falhou: aceitou {ruim}")
        except ValueError: pass
print("ok")
