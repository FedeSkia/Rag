FROM python:3.11-slim

ARG APP_ENV
ENV APP_ENV=$APP_ENV

ENV APP_ENV="$APP_ENV" \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

# ---- OS deps for PDF/OCR/Camelot/OpenCV ----
# - poppler-utils: pdfinfo/pdftoppm (fixes your error)
# - ghostscript: Camelot (lattice) backend
# - tesseract-ocr (+ optional ita lang pack)
# - libgl/libx* libs: needed by opencv (camelot-py[cv] pulls it in)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl \
    poppler-utils ghostscript tesseract-ocr \
    libglib2.0-0 libsm6 libxrender1 libxext6 libgl1 \
    libpq5 libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN if [ "$INSTALL_TESSERACT_ITA" = "true" ]; then \
      apt-get update && apt-get install -y --no-install-recommends tesseract-ocr-ita && \
      rm -rf /var/lib/apt/lists/* ; \
    fi

# ---- Install Poetry ----
RUN pip install --no-cache-dir "poetry==1.8.3" && poetry --version

# ---- Copy entrypoint + env file ----
COPY docker/rag_app/entrypoint_app.sh .
RUN chmod +x /app/entrypoint_app.sh
# APP_ENV should be a filename like .env.prod.docker available in build context
COPY ${APP_ENV} ./

# ---- Install Python deps with Poetry (cache-friendly layer) ----
# Copy only lock files first to leverage Docker layer cache on deps
COPY pyproject.toml ./
COPY README.md ./
COPY src /app/src

RUN poetry config warnings.export false && poetry debug info && cat pyproject.toml
RUN poetry lock
RUN poetry install --no-ansi --only main

# ---- Default entrypoint ----
ENTRYPOINT ["/app/entrypoint_app.sh"]
