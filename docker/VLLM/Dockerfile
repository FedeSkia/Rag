# syntax=docker/dockerfile:1.7

ARG VLLM_IMAGE=vllm/vllm-openai:latest
ARG MODEL=Qwen/Qwen2.5-3B-Instruct

# Base image with vLLM server
FROM ${VLLM_IMAGE} as base
USER root
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates \
  && rm -rf /var/lib/apt/lists/*
ENV HOST=0.0.0.0 PORT=8000 \
    VLLM_GPU_MEMORY_UTILIZATION=0.9 VLLM_MAX_MODEL_LEN=8192
EXPOSE 8000

# Stage that downloads model into /model
FROM base as downloader
ARG MODEL
# BuildKit: pass your HF token with --secret id=hf_token,env=HUGGING_FACE_HUB_TOKEN
RUN pip install -U "huggingface_hub[cli]"

RUN --mount=type=secret,id=hf_token \
    bash -lc 'set -e; \
      mkdir -p /model && \
      huggingface-cli download "$MODEL" --local-dir /model --exclude \"original/*\"'

# Final image: copy model in and serve from local path
FROM base
COPY --from=downloader /model /model
ENV MODEL_DIR=/model

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD curl -fsS "http://127.0.0.1:${PORT}/v1/models" || exit 1

ENTRYPOINT ["bash","-lc","python -m vllm.entrypoints.openai.api_server \
  --model ${MODEL_DIR} \
  --host ${HOST} --port ${PORT} \
  --gpu-memory-utilization ${VLLM_GPU_MEMORY_UTILIZATION} \
  --max-model-len ${VLLM_MAX_MODEL_LEN}"]
