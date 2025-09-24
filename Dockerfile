# ======================================================================================
#    SENTIRIC PYTHON SERVICE - STANDART DOCKERFILE v2.3 (Robust Permissions)
# ======================================================================================
ARG PYTHON_VERSION=3.11
ARG BASE_IMAGE_TAG=${PYTHON_VERSION}-slim-bullseye

# STAGE 1: BUILDER
FROM python:${BASE_IMAGE_TAG} AS builder
WORKDIR /app
ENV PIP_BREAK_SYSTEM_PACKAGES=1 PIP_NO_CACHE_DIR=1 POETRY_NO_INTERACTION=1 POETRY_VIRTUALENVS_IN_PROJECT=true \
    # Cache yolunu builder içinde /tmp gibi geçici bir yere yönlendiriyoruz.
    # Bu, modellerin indirilmesini sağlar, ancak nihai imaja bu cache'i taşımayacağız.
    # Model indirme işlemini runtime'da, doğru izinlerle yapacağız.
    HF_HOME="/tmp/hf_cache"

RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg && \
    pip install --no-cache-dir --upgrade pip poetry && \
    rm -rf /var/lib/apt/lists/*
COPY poetry.lock pyproject.toml ./
RUN poetry install --without dev --no-root --sync

# STAGE 2: PRODUCTION
FROM python:${BASE_IMAGE_TAG}
WORKDIR /app
ARG GIT_COMMIT="unknown"
ARG BUILD_DATE="unknown"
ARG SERVICE_VERSION="0.0.0"
ENV GIT_COMMIT=${GIT_COMMIT} BUILD_DATE=${BUILD_DATE} SERVICE_VERSION=${SERVICE_VERSION} \
    PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH" HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    # --- KRİTİK DEĞİŞİKLİK: HF_HOME'u appuser'ın ev dizinine yönlendiriyoruz ---
    HF_HOME="/home/appuser/.cache/huggingface"

RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd curl ca-certificates ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 appgroup && \
    # --- KRİTİK DEĞİŞİKLİK: appuser için bir ev dizini (/home/appuser) oluşturuyoruz ---
    adduser --system --home /home/appuser --uid 1001 --ingroup appgroup appuser

COPY --from=builder --chown=appuser:appgroup /app/.venv ./.venv
COPY --chown=appuser:appgroup ./app ./app
COPY --chown=appuser:appgroup ./app/static ./app/static
COPY --chown=appuser:appgroup ./app/templates ./app/templates

# --- NİHAİ İZİN DÜZELTMESİ ---
# /home/appuser dizinini oluştur ve sahipliğini appuser'a ver.
# Bu, HF_HOME'un yazılabilir olmasını GARANTİ EDER.
RUN mkdir -p /home/appuser/.cache/huggingface && \
    chown -R appuser:appgroup /home/appuser
# --- DÜZELTME SONU ---

USER appuser
EXPOSE 7860
# Portu HF için 7860, yerel için 15010 olarak ayarla
# Bu, HF Dockerfile'ında override edilecek.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "15010", "--no-access-log"]