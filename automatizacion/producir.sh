#!/bin/bash
# Produce the Spanish and English versions of one short from its guion.json.
# usage: automatizacion/producir.sh <carpeta con guion.json> [es en]
# Needs PIXABAY_API_KEY in the environment and the music in $MUSICA (default: ../datos/assets/musica).
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd); S=$ROOT/scripts; FF=$S/node_modules/ffmpeg-static/ffmpeg
DIR=$(cd "$1" && pwd); shift; LANGS=${*:-es en}
# CI checks datos out inside the motor; locally it sits next to it
MUSICA=${MUSICA:-$( [ -d "$ROOT/datos" ] && echo "$ROOT/datos" || echo "$ROOT/../datos" )/assets/musica}
PY=${PY:-python3}
# one track per short, picked from the slug so both languages share it
TRACKS=("$MUSICA"/*-FULL.mp3); N=$(( $(basename "$DIR" | cksum | cut -d' ' -f1) % ${#TRACKS[@]} )); MUSIC=${TRACKS[$N]}
mkdir -p "$DIR/entrega"
for L in $LANGS; do
  W=$DIR/trabajo_$L
  "$PY" "$S/montar.py" "$DIR/guion.json" "$L" "$W" "$FF" "$MUSIC"
  (cd "$S" && node render.js "$FF" "$W/timeline.json" "$W/audio.wav" "$DIR/entrega/$L.mp4")
done
ls -la "$DIR/entrega"
