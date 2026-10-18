#!/bin/bash
# Gera Tempo.app (rodar no Mac, com Python 3.11+)
set -e
cd "$(dirname "$0")"
ICON_ARGS=""
if [ -f icon.png ]; then
  # ícone do app = mesmo relógio do Tempo (PNG -> .icns)
  rm -rf Tempo.iconset && mkdir Tempo.iconset
  for s in 16 32 128 256 512; do
    sips -z $s $s icon.png --out Tempo.iconset/icon_${s}x${s}.png >/dev/null
    d=$((s*2)); sips -z $d $d icon.png --out Tempo.iconset/icon_${s}x${s}@2x.png >/dev/null
  done
  iconutil -c icns Tempo.iconset -o Tempo.icns
  ICON_ARGS="--icon Tempo.icns"
fi
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pyinstaller --noconfirm --windowed --name Tempo $ICON_ARGS main.py
echo "Pronto: dist/Tempo.app"
