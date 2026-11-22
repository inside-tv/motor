#!/bin/bash
# Save a secret in the GitHub repo without it ever showing in the chat: asks for it hidden (or reads a credentials file).
# usage: bash automatizacion/subir_secreto.sh NOMBRE     (YT_TOKEN_ES / YT_TOKEN_EN / YT_CLIENT_SECRET read their file)
set -euo pipefail
cd "$(dirname "$0")/.."; N=${1:?nombre del secreto}
case "$N" in
  YT_TOKEN_ES) gh secret set "$N" < credenciales/youtube_token_es.json ;;
  YT_TOKEN_EN) gh secret set "$N" < credenciales/youtube_token_en.json ;;
  YT_CLIENT_SECRET) gh secret set "$N" < credenciales/youtube_client_secret.json ;;
  *) read -rsp "Pega el valor de $N (no se verá) y pulsa Enter: " v; echo; printf '%s' "$v" | gh secret set "$N" ;;
esac
echo "secreto $N guardado"
