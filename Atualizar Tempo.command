#!/bin/bash
# Primeira vez (ou quando quiser na mão): cria o certificado que mantém as permissões do app
# entre atualizações e instala a versão desta pasta. Depois disso o app se atualiza sozinho.
cd "$(dirname "$0")" || exit 1
if ! security find-certificate -c "Tempo Local" >/dev/null 2>&1; then
  echo "Criando o certificado do Tempo (uma vez só; o Mac pode pedir sua senha)…"
  T="$(mktemp -d)"
  cat > "$T/c.cnf" <<'CNF'
[req]
distinguished_name=dn
x509_extensions=ext
prompt=no
[dn]
CN=Tempo Local
[ext]
keyUsage=critical,digitalSignature
extendedKeyUsage=critical,codeSigning
basicConstraints=critical,CA:false
CNF
  /usr/bin/openssl req -x509 -newkey rsa:2048 -nodes -days 3650 -config "$T/c.cnf" -keyout "$T/k.pem" -out "$T/c.pem" >/dev/null 2>&1 \
    && /usr/bin/openssl pkcs12 -export -inkey "$T/k.pem" -in "$T/c.pem" -out "$T/t.p12" -passout pass:tempo >/dev/null 2>&1 \
    && security import "$T/t.p12" -k ~/Library/Keychains/login.keychain-db -P tempo -T /usr/bin/codesign >/dev/null \
    && security add-trusted-cert -r trustRoot -p codeSign -k ~/Library/Keychains/login.keychain-db "$T/c.pem" \
    && echo "Certificado criado." || echo "Não consegui criar o certificado; o app funciona, mas pode pedir o acesso ao disco de novo após atualizar."
  rm -rf "$T"
fi
echo "Gerando e instalando o Tempo…"
rm -f .atualizar_falhou
if ./atualizar.sh; then echo "Pronto."; else echo "Não deu certo:"; tail -20 build.log; read -n 1 -s -r -p "Aperte uma tecla para fechar."; fi
