# Updates Infos — Tempo para Mac



## V2.03.16 (16/11/2026)
- **Atualização automática:** o app compara a própria versão com o arquivo VERSION da pasta ~/tempo-build. Se houver versão nova, se atualiza sozinho (ao abrir, ou depois de 5 min parado / tela bloqueada) com atualizar.sh, e reabre.
- **Botão no site:** "Atualizar app do Mac" aparece no rodapé da barra lateral quando há versão nova.
- **Assinatura estável:** o certificado "Tempo Local" (criado pelo Atualizar Tempo.command na primeira vez) mantém o Acesso Total ao Disco entre atualizações.
- **Se falhar:** grava build.log e atualizar.log e não tenta a mesma versão de novo até a pasta mudar.

## V2.03.15 (16/11/2026)
- **Site aberto pelo app:** produção (https://apptempo-abon.vercel.app), não mais a prévia da V2.02.122.
- **WhatsApp (wa.py):** conta as mensagens enviadas por contato e dia (nunca lê o texto das mensagens).
- **Notas e comprovantes:** lê PDFs de nota fiscal (texto ou escaneados) e fotos de comprovante nas conversas de terapia, salva cópia no iCloud (Terapias/Ano_Mes) e manda ao site. O item fica na fila até o site confirmar o recebimento.
- **Leitura de imagem:** reconhecimento de texto do próprio macOS (ocrmac), sem enviar documentos para fora.
- **Dependências novas:** pypdf e ocrmac (requirements.txt).

## V2.02.122 (23/10/2026) — build de teste
- **Site aberto pelo app:** aponta para a prévia Vercel da branch `chatgpt/v2.02.122`, não para a produção.
- **Compatibilidade:** versão sincronizada com o site V2.02.122.
- **Cmd+J:** mantém captura da tela inteira com a seleção desenhada pela interface; precisa de validação manual no macOS com clique e arrasto.
- **Arquivos alterados:** `main.py`, `VERSION`, `README.md`.
- **Build:** ainda precisa ser executado no Mac local; este ambiente não compila nem testa o aplicativo nativo.
- **Importante:** este é um build separado para teste. Não substituir a instalação oficial até validar o site, a captura de tela e as permissões do macOS.
