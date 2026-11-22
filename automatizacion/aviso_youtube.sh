#!/bin/bash
# While the YouTube API audit is pending: put both videos of a production folder in a release of the PRIVATE datos repo
# and comment in its open issue "Pendientes de subir a YouTube" with titles and descriptions. GitHub emails each comment.
# Nothing goes to this (public) repository: no artifacts, no logs with the texts.
# usage: automatizacion/aviso_youtube.sh <datos/produccion/carpeta>     Needs GH_TOKEN with access to DATOS_REPO.
set -euo pipefail
DIR=${1:?carpeta}; REPO=${DATOS_REPO:?falta DATOS_REPO}; TAG="v-$(basename "$DIR" | tr '_' '-')"
TITLE="Pendientes de subir a YouTube"
gh release create "$TAG" -R "$REPO" --title "$(basename "$DIR")" --notes "Videos para subir a mano" "$DIR"/entrega/*.mp4 >/dev/null
NUM=$(gh issue list -R "$REPO" --state open --search "\"$TITLE\" in:title" --json number -q '.[0].number' 2>/dev/null || true)
if [ -z "$NUM" ]; then
  NUM=$(gh issue create -R "$REPO" --title "$TITLE" --body "Mientras la auditoría de la API de YouTube no esté aprobada, los videos se suben a mano.
1. Descarga los mp4 del release enlazado en cada comentario.
2. YouTube Studio del canal correcto (Adentro = es, Inside = en) → Crear → Subir videos → pega título, descripción y etiquetas.
3. Contenido alterado o sintético: **Sí**.
4. Marca el comentario con 👍 cuando esté subido." | grep -o '[0-9]*$')
fi
body="### 📦 $(basename "$DIR")
**Descarga:** https://github.com/$REPO/releases/tag/$TAG
"
for L in es en; do
  f="$DIR/entrega/$L.json"; [ -f "$f" ] || continue
  body+="
#### ${L^^} — $( [ $L = es ] && echo Adentro || echo Inside )
$(python3 -I -c 'import json,sys; m=json.load(open(sys.argv[1])); print("**Título:** "+m["title"]+"\n\n**Descripción:**\n"+m["description"]+"\n\n**Etiquetas:** "+", ".join(m.get("tags",[])))' "$f")
"
done
gh issue comment "$NUM" -R "$REPO" --body "$body" >/dev/null
echo "aviso publicado (issue #$NUM)"
