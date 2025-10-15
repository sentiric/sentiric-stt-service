### 📄 File: stt-service/Dockerfile (NİHAİ DÜZELTME)

ARG PYTHON_VERSION=3.11
ARG BASE_IMAGE_TAG=${PYTHON_VERSION}-slim-bullseye

# ==================================
#      Aşama 1: Builder
# ==================================
FROM python:${BASE_IMAGE_TAG} AS builder

WORKDIR /app

# --- KAPSAMLI SİSTEM BAĞIMLILIKLARI ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ffmpeg \
    pkg-config \
    libavcodec-dev \
    libavdevice-dev \
    libavfilter-dev \
    libavformat-dev \
    libavutil-dev \
    libswresample-dev \
    libswscale-dev \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
# --- DEĞİŞİKLİK SONU ---

RUN pip install --no-cache-dir --upgrade pip poetry
ENV POETRY_VIRTUALENVS_IN_PROJECT=true
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev --no-root


# ==================================
#      Aşama 2: Final Image
# ==================================
FROM python:${BASE_IMAGE_TAG} AS final

WORKDIR /app

ARG GIT_COMMIT="unknown"
ARG BUILD_DATE="unknown"
ARG SERVICE_VERSION="0.0.0"
ENV GIT_COMMIT=${GIT_COMMIT} BUILD_DATE=${BUILD_DATE} SERVICE_VERSION=${SERVICE_VERSION} PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH" HF_HUB_DISABLE_SYMLINKS_WARNING=1 HF_HOME="/tmp/huggingface_cache"

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg netcat-openbsd curl ca-certificates && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 appgroup && adduser --system --no-create-home --uid 1001 --ingroup appgroup appuser

COPY --from=builder --chown=appuser:appgroup /app/.venv ./.venv
COPY --chown=appuser:appgroup ./app ./app
COPY --chown=appuser:appgroup ./app/static ./app/static
COPY --chown=appuser:appgroup ./app/templates ./app/templates

USER appuser
EXPOSE 15010 15011 15012
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "15010", "--no-access-log"]