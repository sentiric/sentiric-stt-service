# --- STAGE 1: Builder ---
FROM python:3.11-slim-bullseye AS builder

WORKDIR /app

ENV HF_HOME=/app/cache/huggingface \
    PIP_BREAK_SYSTEM_PACKAGES=1

# Sistem derleme araçları ve ses işleme için ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends build-essential ffmpeg && rm -rf /var/lib/apt/lists/*

# Sadece CPU için torch kurarak imaj boyutunu küçült
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Bağımlılıkları kur
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Modeli build sırasında indirerek çalışma zamanı gecikmesini önle
RUN python -c "from transformers import pipeline; pipeline('automatic-speech-recognition', model='openai/whisper-base')"


# --- STAGE 2: Production ---
FROM python:3.11-slim-bullseye

WORKDIR /app

ENV HF_HOME=/app/cache/huggingface \
    NO_COLOR=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1

# Sistem çalışma zamanı bağımlılıklarını (ffmpeg) kur
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Builder'dan sadece kurulu Python paketlerini kopyala
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Builder'dan indirilmiş ve cache'lenmiş modeli kopyala
COPY --from=builder ${HF_HOME} ${HF_HOME}

# Uygulama kodunu kopyala
COPY ./app ./app

EXPOSE 5001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5001"]