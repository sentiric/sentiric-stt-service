# ======================================================================================
#    SENTIRIC PYTHON SERVICE - STANDART DOCKERFILE v2.1 (Universal Cache)
# ======================================================================================
ARG PYTHON_VERSION=3.11
ARG BASE_IMAGE_TAG=${PYTHON_VERSION}-slim-bullseye

# STAGE 1: BUILDER
FROM python:${BASE_IMAGE_TAG} AS builder
WORKDIR /app
ENV PIP_BREAK_SYSTEM_PACKAGES=1 PIP_NO_CACHE_DIR=1 POETRY_NO_INTERACTION=1 POETRY_VIRTUALENVS_IN_PROJECT=true \
    HF_HOME="/app/data/.cache/huggingface"
RUN apt-get update && apt-get install -y --no-install-recommends curl ffmpeg && \
    pip install --no-cache-dir --upgrade pip poetry && \
    rm -rf /var/lib/apt/lists/*
COPY poetry.lock pyproject.toml ./
RUN mkdir -p ${HF_HOME}
RUN poetry install --without dev --no-root --sync

# STAGE 2: PRODUCTION
FROM python:${BASE_IMAGE_TAG}
WORKDIR /app
ARG GIT_COMMIT="unknown"
ARG BUILD_DATE="unknown"
ARG SERVICE_VERSION="0.0.0"
ENV GIT_COMMIT=${GIT_COMMIT} BUILD_DATE=${BUILD_DATE} SERVICE_VERSION=${SERVICE_VERSION} \
    PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH" HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    HF_HOME="/app/data/.cache/huggingface"
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd curl ca-certificates ffmpeg \
    && rm -rf /var/lib/apt/lists/*
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --no-create-home --uid 1001 --ingroup appgroup appuser
COPY --from=builder --chown=appuser:appgroup /app/.venv ./.venv
COPY --from=builder --chown=appuser:appgroup /app/data /app/data
COPY --chown=appuser:appgroup ./app ./app
COPY --chown=appuser:appgroup ./app/static ./app/static
COPY --chown=appuser:appgroup ./app/templates ./app/templates
RUN chown -R appuser:appgroup /app/data
USER appuser
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "15010", "--no-access-log"]