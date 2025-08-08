# ⚡ Sentiric STT Service (Speech-to-Text)

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Sentiric STT Service**, Sentiric "İletişim İşletim Sistemi" ekosisteminin "kulakları" olarak görev yapan, yüksek performanslı ve modüler bir yapay zeka servisidir. Temel amacı, gelen ses akışlarını veya dosyalarını yüksek doğrulukla metne dönüştürmektir.

Bu servis, "en küçük sistemde en yüksek performans" hedefiyle tasarlanmış olup, minimum kaynak tüketimiyle gerçek zamanlıya yakın (near real-time) transkripsiyon yeteneği sunar.

## ✨ Temel Özellikler

*   **Yüksek Performans:** `faster-whisper` (CTranslate2) motoru sayesinde, standart `transformers` kütüphanesine göre CPU'da **4 kata kadar daha hızlı** çalışır ve **%50 daha az bellek** kullanır.
*   **Otomatik Dil Tespiti:** Herhangi bir konfigürasyon olmadan birden fazla dili (Türkçe, İngilizce vb.) otomatik olarak algılar ve metne döker.
*   **Kaynak Verimliliği:** `int8` kuantizasyon desteği ile optimize edilmiştir. Rölantide **~200MB RAM** kullanımıyla en mütevazı sunucularda bile çalışabilir.
*   **"Tak-Çıkar" Mimarisi:** Temel felsefemize uygun olarak, farklı STT motorlarını (adaptörlerini) `.env` dosyası üzerinden kolayca değiştirebilecek esnek bir yapıya sahiptir.
*   **Gözlemlenebilirlik:** Prometheus metrikleri ve ortama duyarlı (JSON/Console) yapılandırılmış loglama ile üretime hazırdır.

## 🚀 Hızlı Başlangıç (Docker ile)

Bu servisi çalıştırmanın en hızlı ve önerilen yolu Docker'dır.

1.  **Repo'yu Klonlayın:**
    ```bash
    git clone https://github.com/sentiric/sentiric-stt-service.git
    cd sentiric-stt-service
    ```

2.  **Ortam Dosyasını Oluşturun:**
    ```bash
    # .env.docker dosyasını projenin ana dizinine .env olarak kopyalayın
    # Genellikle bu, sentiric-infrastructure reposundan yönetilir.
    # Şimdilik, docker-compose.service.yml'nin .env.docker'ı okuduğunu varsayıyoruz.
    ```

3.  **Servisi Başlatın:**
    ```bash
    docker compose -f docker-compose.service.yml up --build -d
    ```
    İlk başlatmada, model indirileceği için bu işlem birkaç dakika sürebilir. Sonraki başlatmalar anında olacaktır.

4.  **Sağlık Durumunu Kontrol Edin:**
    ```bash
    curl http://localhost:5001/health
    ```
    Başarılı bir yanıt şöyle görünmelidir:
    ```json
    {"status":"ok","adapter_loaded":true,"adapter_type":"faster_whisper"}
    ```

## 🎤 API Kullanımı

Servis, ses dosyalarını metne dönüştürmek için tek bir ana endpoint sunar.

**Endpoint:** `POST /api/v1/transcribe`
**Gövde:** `multipart/form-data`
**Parametre:** `audio_file` (Ses dosyası)

### `curl` ile Örnek Kullanım

```bash
curl -X POST \
  -F "audio_file=@path/to/your/audio.wav;type=audio/wav" \
  http://localhost:5001/api/v1/transcribe
```

**Başarılı Yanıt (`200 OK`):**
```json
{
  "text": "Bu, ses dosyasının içindeki metindir."
}
```

**Hatalı Yanıt (`400 Bad Request`):**
```json
{
  "detail": "Geçersiz dosya tipi. Lütfen bir ses dosyası (.wav, .mp3 vb.) yükleyin."
}
```

## 🛠️ Mimari ve Tasarım Kararları

*   **Teknoloji Yığını:** Python 3.11, FastAPI, Uvicorn, Faster-Whisper, CTranslate2.
*   **Adaptör Deseni:** Servisin kalbi, `app/services/adapters` altında bulunan adaptörlerdir. Bu yapı, `faster-whisper`'ı gelecekte `whisper.cpp` veya bulut tabanlı bir API (örn: Google Speech-to-Text) ile kolayca değiştirmemize olanak tanır. Hangi adaptörün kullanılacağı `.env` dosyasındaki `STT_ADAPTER` değişkeni ile belirlenir.
*   **Paketleme ve Bağımlılık Yönetimi:** Proje, modern Python standartlarına uygun olarak `pyproject.toml` ile yönetilmektedir. Bu, hem geliştirme hem de Docker build süreçlerinde tutarlılık sağlar.
*   **Test Stratejisi:** Projenin kalitesi, `pytest` ile yazılmış ve `tests/` klasöründe bulunan birim ve entegrasyon testleri ile garanti altına alınmıştır.

## 💻 Yerel Geliştirme Ortamı

1.  Python 3.11+ kurulu olduğundan emin olun.
2.  Bir sanal ortam (virtual environment) oluşturun:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```
3.  Projeyi "düzenlenebilir modda" ve geliştirme bağımlılıklarıyla birlikte kurun:
    ```bash
    pip install -e ".[dev]"
    ```
4.  `.env` dosyanızı oluşturun ve gerekli değişkenleri ayarlayın.
5.  Servisi başlatın:
    ```bash
    uvicorn app.main:app --reload
    ```
6.  Testleri çalıştırın:
    ```bash
    pytest -v
    ```
---
