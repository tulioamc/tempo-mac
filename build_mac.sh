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
# versão do app = versão do site (arquivo VERSION, igual ao APP_VERSION do Tempo)
V="$(tr -d '[:space:]' < VERSION)"
PL="dist/Tempo.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString $V" "$PL" || /usr/libexec/PlistBuddy -c "Add :CFBundleShortVersionString string $V" "$PL"
/usr/libexec/PlistBuddy -c "Set :CFBundleVersion $V" "$PL" || /usr/libexec/PlistBuddy -c "Add :CFBundleVersion string $V" "$PL"
echo "Pronto: dist/Tempo.app ($V)"
