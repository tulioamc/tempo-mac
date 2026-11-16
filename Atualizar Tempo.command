#!/bin/bash
# Dois cliques: gera o app do Mac, troca o que está em Aplicativos e abre de novo.
cd "$(dirname "$0")" || exit 1
echo "Gerando o Tempo…"
if ! ./build_mac.sh > build.log 2>&1; then
  echo ""
  echo "Não deu certo. As últimas linhas do registro:"
  tail -20 build.log
  read -n 1 -s -r -p "Aperte uma tecla para fechar."
  exit 1
fi
echo "Fechando o Tempo aberto…"
osascript -e 'tell application "Tempo" to quit' >/dev/null 2>&1
sleep 2
pkill -x Tempo >/dev/null 2>&1
rm -rf /Applications/Tempo.app ~/Applications/Tempo.app
cp -R dist/Tempo.app /Applications/
echo "Abrindo a versão $(cat VERSION)…"
open /Applications/Tempo.app
sleep 1
osascript -e 'tell application "Terminal" to close (every window whose name contains "Atualizar Tempo")' >/dev/null 2>&1 &
exit 0
