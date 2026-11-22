#!/bin/bash
# Prepare an Ubuntu runner: emoji font, node packages (canvas, ffmpeg) and edge-tts. No AI models to download.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
sudo apt-get install -y -qq fonts-noto-color-emoji >/dev/null 2>&1 || true
[ -f /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf ] || { sudo mkdir -p /usr/share/fonts/truetype/noto; sudo ln -sf "$(fc-list | grep -m1 NotoColorEmoji | cut -d: -f1)" /usr/share/fonts/truetype/noto/NotoColorEmoji.ttf; }
cd "$ROOT/scripts" && npm install --no-audit --no-fund --silent
python3 -m pip install -q -r requirements.txt
echo listo
