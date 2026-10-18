#!/bin/bash
# Gera Tempo.app (rodar no Mac, com Python 3.11+)
set -e
cd "$(dirname "$0")"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pyinstaller --noconfirm --windowed --name Tempo main.py
echo "Pronto: dist/Tempo.app"
