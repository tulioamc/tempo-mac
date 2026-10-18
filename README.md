# Tempo para Mac

Janela nativa que abre https://apptempo-abon.vercel.app e grava as notas e comprovantes
de Terapias na pasta do iCloud (`Terapias/<Ano_Mes>/`).

## Rodar no Mac
    python3 -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    python main.py

## Gerar o app
    ./build_mac.sh      # cria dist/Tempo.app

## Testar a parte do iCloud (sem janela)
    python3 test_icloud.py

## Ociosidade (item 5 do backlog)
- `idle.py` lê o tempo parado do Mac (`ioreg`, HIDIdleTime) e o app em uso (`osascript`).
- Tela bloqueada conta como parada (`CGSSessionScreenIsLocked`).
- Uso do WhatsApp em primeiro plano vira aviso de pausa depois do fato: ao sair do app, chama `reportIdle` com app "WhatsApp". O site só sugere se o trecho tiver pelo menos o limite de minutos.
- Quando fica parado 5 min e volta a usar, chama `window.TempoBridge.reportIdle(início, fim, app)` no site, que cria a sugestão de pausa (Aceitar/Ignorar).
- Testar: `python3 test_idle.py` (lógica, em qualquer sistema).
- Na primeira vez, o macOS pede permissão de Automação para o "System Events" (necessária para ler o app em uso).
- Se a janela estiver fechada ou o site não carregado no momento, a pausa não chega ao site. Próximo passo: guardar pendentes e reenviar.

## Ainda não ligado
- O site ainda não chama `window.pywebview.api.salvar_terapia` (upload no Terapias).
- Leitura de valor/terapeuta por OCR.
- Ícone na barra de menus, atalho global e cronômetro (itens S1–S7 do backlog).
- Ociosidade, tela bloqueada e WhatsApp: ainda não testados no Mac real (só a lógica).
- Registro de programa e arquivo por pasta e proposta de fim de dia: ainda não feito.
