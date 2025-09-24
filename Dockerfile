# ======================================================================================
#    SENTIRIC PYTHON SERVICE - STANDART DOCKERFILE v2.0
# ======================================================================================

# --- GLOBAL BUILD ARGÜMANLARI ---
ARG PYTHON_VERSION=3.11
ARG BASE_IMAGE_TAG=${PYTHON_VERSION}-slim-bullseye

# ======================================================================================
#    STAGE 1: BUILDER - Bağımlılıkları kurar
# ======================================================================================
FROM python:${BASE_IMAGE_TAG} AS builder

WORKDIR /app

ENV PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true

# Gerekli sistem bağımlılıkları ve Poetry kurulumu
RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
    rm -rf /var/lib/apt/lists/*

# Sadece bağımlılık tanımlarını kopyala ve kur (Docker build cache'ini optimize eder)
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev --no-root --sync

# ======================================================================================
#    STAGE 2: PRODUCTION - Hafif ve güvenli imaj
# ======================================================================================
FROM python:${BASE_IMAGE_TAG}

WORKDIR /app

# Build-time bilgileri
ARG GIT_COMMIT="unknown"
ARG BUILD_DATE="unknown"
ARG SERVICE_VERSION="0.0.0"
ENV GIT_COMMIT=${GIT_COMMIT} \
    BUILD_DATE=${BUILD_DATE} \
    SERVICE_VERSION=${SERVICE_VERSION} \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1

# Çalışma zamanı sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* 

# Root olmayan kullanıcı oluştur
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --no-create-home --uid 1001 --ingroup appgroup appuser

# Bağımlılıkları ve uygulama kodunu kopyala
COPY --from=builder --chown=appuser:appgroup /app/.venv ./.venv
COPY --chown=appuser:appgroup ./app ./app
# STT servisinin ihtiyaç duyduğu statik dosyaları kopyala
COPY --chown=appuser:appgroup ./app/static ./app/static
COPY --chown=appuser:appgroup ./app/templates ./app/templates


# Sahipliği ayarla ve kullanıcıyı değiştir
USER appuser

# stt-service için varsayılan komut
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "15010", "--no-access-log"]