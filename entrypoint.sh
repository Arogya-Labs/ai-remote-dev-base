#!/bin/bash
set -e

mkdir -p /home/dev/logs

# Start Ollama
echo "Starting Ollama..."
ollama serve > /home/dev/logs/ollama.log 2>&1 &

# Start Open WebUI
echo "Starting Open WebUI..."
uv run open-webui serve > /home/dev/logs/openwebui.log 2>&1 &

# Keep the container alive and show logs
tail -f /home/dev/logs/*.log
