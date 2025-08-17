#!/bin/bash
set -euo pipefail

echo "Starting Ollama..."

# If /root/.ollama is empty (e.g., fresh EFS or Docker volume), seed it from the baked copy
if [ -d "/root/.ollama" ] && [ -z "$(ls -A /root/.ollama)" ]; then
  if [ -d "/opt/ollama-models" ] && [ -n "$(ls -A /opt/ollama-models)" ]; then
    echo "Seeding empty /root/.ollama from /opt/ollama-models..."
    cp -a /opt/ollama-models/. /root/.ollama/
  else
    echo "Warning: /opt/ollama-models is empty or missing; nothing to seed."
  fi
fi

# Start server
ollama serve &
OLLAMA_PID=$!

# Wait for readiness
echo "Waiting for Ollama to be ready..."
for i in $(seq 1 60); do
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; then
    echo "Ollama ready."
    break
  fi
  echo "  ...not ready yet"
  sleep 1
done

echo "Installed models:"
ollama list || true

wait $OLLAMA_PID
