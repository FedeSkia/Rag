# syntax=docker/dockerfile:1
FROM ollama/ollama:latest

# ---- Configure which models to bake into the image at build time ----
# Space-separated list, e.g.:
#   --build-arg OLLAMA_MODELS="qwen3:0.6b qwen2:0.5b"
ARG OLLAMA_MODELS="qwen3:0.6b"

# Tools used during build for readiness checks
RUN apt-get update && apt-get install -y curl bash && rm -rf /var/lib/apt/lists/*

# ---- Preload models during the build ----
# We start the ollama server, wait until /api/tags responds,
# then `ollama pull` each model listed in $OLLAMA_MODELS.
# Finally, we keep a *read-only copy* at /opt/ollama-models for seeding volumes later.
RUN bash -lc 'set -euo pipefail; \
  echo "Preloading models: ${OLLAMA_MODELS}"; \
  /usr/bin/ollama serve >/tmp/ollama-build.log 2>&1 & \
  pid=$!; \
  for i in $(seq 1 60); do \
    if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null; then \
      echo "Ollama is ready (build phase)"; \
      break; \
    fi; \
    sleep 1; \
  done; \
  for m in ${OLLAMA_MODELS}; do \
    echo "Pulling $m ..."; \
    /usr/bin/ollama pull "$m"; \
  done; \
  echo "Stopping build-time ollama (pid=$pid)"; \
  kill $pid || true; \
  wait $pid || true; \
  mkdir -p /opt/ollama-models; \
  cp -a /root/.ollama/. /opt/ollama-models/; \
  echo "Preload complete."'

# ---- Runtime files ----
COPY entrypoint_ollama.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 11434

# Keep the volume declaration if you want persistence across task restarts.
# NOTE: If you *do* mount a volume/EFS here, the entrypoint will seed it if empty.
VOLUME ["/root/.ollama"]

ENTRYPOINT ["/entrypoint.sh"]
