# ======================================================================================
#    SENTIRIC PYTHON SERVICE - STANDART DOCKERFILE v2.4 (Runtime Permissions Fix)
# ======================================================================================
ARG PYTHON_VERSION=3.11
ARG BASE_IMAGE_TAG=${PYTHON_VERSION}-slim-bullseye

# STAGE 1: BUILDER
FROM python:${BASE_IMAGE_TAG} AS builder
WORKDIR /app
ENV PIP_BREAK_SYSTEM_PACKAGES=1 PIP_NO_CACHE_DIR=1 POETRY_NO_INTERACTION=1 POETRY_VIRTUALENVS_IN_PROJECT=true
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
    HF_HOME="/home/appuser/.cache/huggingface"

# --- YENİ: gosu (kullanıcı değiştirmek için) ve sudo'yu ekliyoruz ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd curl ca-certificates ffmpeg gosu sudo \
    && rm -rf /var/lib/apt/lists/*

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --home /home/appuser --uid 1001 --ingroup appgroup appuser
# appuser'ın sudoers grubuna eklenmesi (opsiyonel ama HF'de bazen gerekli)
RUN echo "appuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

COPY --from=builder --chown=appuser:appgroup /app/.venv ./.venv
COPY --chown=appuser:appgroup ./app ./app
COPY --chown=appuser:appgroup ./app/static ./app/static
COPY --chown=appuser:appgroup ./app/templates ./app/templates

# --- YENİ: Entrypoint script'ini kopyala ve çalıştırılabilir yap ---
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Çalıştırma anında izinleri düzeltmek için root olarak başla, sonra kullanıcı değiştir
USER root
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "15010", "--no-access-log"]