# --- STAGE 1: Builder ---
FROM python:3.11-slim-bullseye AS builder

# Build argümanlarını build aşamasında kullanılabilir yap
ARG GIT_COMMIT="unknown"
ARG BUILD_DATE="unknown"
ARG SERVICE_VERSION="0.0.0"

WORKDIR /app

# Ortam değişkenleri
ENV PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_NO_CACHE_DIR=1

# Gerekli sistem bağımlılıkları
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ffmpeg && rm -rf /var/lib/apt/lists/*

# --- Standart ve Doğru Kurulum Yöntemi ---
# Önce projenin kurulum tanımını kopyala
COPY pyproject.toml .

# Ardından projenin kendisini (uygulama kodu ve README dahil) kopyala
# .dockerignore sayesinde .venv gibi gereksiz dosyalar gelmeyecek
COPY app ./app
COPY README.md .

# Şimdi hem bağımlılıkları hem de projeyi tek adımda kur
# Bu, setuptools'un ihtiyaç duyduğu tüm dosyaların mevcut olmasını sağlar
RUN pip install .

# --- STAGE 2: Production ---
FROM python:3.11-slim-bullseye

WORKDIR /app

# Ortam değişkenleri
ENV PIP_BREAK_SYSTEM_PACKAGES=1 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    NO_COLOR=1

# --- Çalışma zamanı sistem bağımlılıkları ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    curl \
    ca-certificates \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* 

# Builder'dan sadece kurulu Python kütüphanelerini kopyala
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Uygulama kodunu kopyala
COPY ./app ./app

# --- DÜZELTME: CMD'yi ENTRYPOINT ve CMD olarak ayırıyoruz ---
# Bu, komutun Docker tarafından her zaman doğru yorumlanmasını sağlar.
ENTRYPOINT ["uvicorn"]
CMD ["app.main:app", "--host", "0.0.0.0", "--port", "15010"]