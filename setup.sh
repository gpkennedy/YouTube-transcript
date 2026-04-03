#!/bin/bash
set -e

python3 -m venv venv
./venv/bin/pip install --quiet youtube-transcript-api yt-dlp
chmod +x transcript

echo "Installation terminée. Utilisation : ./transcript \"<url>\""
