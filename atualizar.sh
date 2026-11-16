#!/bin/bash
# Atualiza o Tempo sem ajuda: gera o app, troca o que está em Aplicativos e reabre.
# Chamado pelo próprio app quando a versão desta pasta (VERSION) é mais nova que a instalada,
# pelo botão "Atualizar app do Mac" no site, ou pelo "Atualizar Tempo.command".
cd "$(dirname "$0")" || exit 1
export PATH="/Library/Frameworks/Python.framework/Versions/3.12/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
LOCK=/tmp/tempo-atualizar.lock
mkdir "$LOCK" 2>/dev/null || exit 0          # já tem uma atualização rodando
trap 'rmdir "$LOCK" 2>/dev/null' EXIT
V="$(tr -d '[:space:]' < VERSION)"
aviso() { osascript -e "display notification \"$1\" with title \"Tempo\"" >/dev/null 2>&1; }
echo "$(date '+%d/%m %H:%M') atualizando para $V" >> atualizar.log
if ! ./build_mac.sh > build.log 2>&1; then
  echo "$V" > .atualizar_falhou                 # não tenta de novo a mesma versão até a pasta mudar
  echo "$(date '+%d/%m %H:%M') falhou (ver build.log)" >> atualizar.log
  aviso "Não consegui atualizar o app para $V."
  exit 1
fi
rm -f .atualizar_falhou
osascript -e 'tell application "Tempo" to quit' >/dev/null 2>&1
for i in $(seq 1 15); do pgrep -x Tempo >/dev/null || break; sleep 1; done
pkill -x Tempo >/dev/null 2>&1; sleep 1
rm -rf /Applications/Tempo.app.old
[ -d /Applications/Tempo.app ] && mv /Applications/Tempo.app /Applications/Tempo.app.old
if cp -R dist/Tempo.app /Applications/; then rm -rf /Applications/Tempo.app.old
else rm -rf /Applications/Tempo.app; mv /Applications/Tempo.app.old /Applications/Tempo.app; fi
rm -rf ~/Applications/Tempo.app
open /Applications/Tempo.app
echo "$(date '+%d/%m %H:%M') ok $V" >> atualizar.log
aviso "App do Mac atualizado para $V."
