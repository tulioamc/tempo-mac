"""Testes da parte de ociosidade (rodam em qualquer sistema, sem janela)."""
from idle import Detector, Trecho, iso, parse_hid_idle, parse_tela_bloqueada

SAIDA = '''
    | |   "HIDIdleTime" = 300000000000
    | |   "Other" = 1
'''


def test_parse():
    assert parse_hid_idle(SAIDA) == 300.0
    assert parse_hid_idle("nada aqui") is None


def test_pausa_detectada_ao_voltar():
    d = Detector(limite_s=300)
    t0 = 1000.0
    assert d.passo(t0, 10, "Chrome") is None           # uso normal
    assert d.passo(t0 + 10, 310, "Chrome") is None      # passou do limite: começa a contar
    assert d.passo(t0 + 20, 320, "Chrome") is None      # continua parado
    r = d.passo(t0 + 400, 5, "Chrome")                  # voltou a usar (5 s atrás)
    inicio, fim, app = r
    assert inicio == 700.0   # 1010 - 310: parado desde antes da primeira leitura longa
    assert fim == 1395.0     # instante da última entrada (1400 - 5)
    assert app == "Chrome"


def test_ociosidade_curta_nao_gera_pausa():
    d = Detector(limite_s=300)
    assert d.passo(0, 120, "X") is None
    assert d.passo(10, 3, "X") is None


def test_iso():
    assert iso(0) == "1970-01-01T00:00:00Z"


def test_tela_bloqueada():
    assert parse_tela_bloqueada('  | "CGSSessionScreenIsLocked" = Yes\n') is True
    assert parse_tela_bloqueada('  | "CGSSessionScreenIsLocked" = No\n') is False
    assert parse_tela_bloqueada("nada") is False


def test_trecho_whatsapp_gera_aviso_ao_sair():
    t = Trecho()
    assert t.passo(0, "Chrome") is None
    assert t.passo(10, "WhatsApp") is None
    assert t.passo(40, "WhatsApp") is None
    assert t.passo(50, "Finder") == (10, 40, "WhatsApp")
    assert t.passo(60, "Finder") is None
