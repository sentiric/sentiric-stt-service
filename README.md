# ⚡ Sentiric STT Service (Speech-to-Text)

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)

**Sentiric STT Service**, Sentiric "İletişim İşletim Sistemi" ekosisteminin "kulakları" olarak görev yapan, yüksek performanslı ve modüler bir yapay zeka servisidir. Temel amacı, gelen ses akışlarını veya dosyalarını yüksek doğrulukla metne dönüştürmektir.

Bu servis, "en küçük sistemde en yüksek performans" hedefiyle tasarlanmış olup, minimum kaynak tüketimiyle gerçek zamanlıya yakın (near real-time) transkripsiyon yeteneği sunar.

## 🎯 Temel Sorumluluklar

*   **Yüksek Performanslı Transkripsiyon:** `faster-whisper` (CTranslate2) motoru sayesinde, standart `transformers` kütüphanesine göre CPU'da **4 kata kadar daha hızlı** çalışır ve **%50 daha az bellek** kullanır.
*   **Otomatik Dil Tespiti:** Herhangi bir konfigürasyon olmadan birden fazla dili (Türkçe, İngilizce vb.) otomatik olarak algılar ve metne döker.
*   **"Tak-Çıkar" Mimarisi:** Temel felsefemize uygun olarak, farklı STT motorlarını (adaptörlerini) `.env` dosyası üzerinden kolayca değiştirebilecek esnek bir yapıya sahiptir.
*   **API Sunucusu:** `/api/v1/transcribe` endpoint'i üzerinden ses dosyalarını kabul eder ve transkripsiyon sonucunu JSON olarak döndürür.

## 🛠️ Teknoloji Yığını

*   **Dil:** Python
*   **Web Çerçevesi:** FastAPI
*   **AI Motoru:** `faster-whisper` (CTranslate2)
*   **Paketleme:** `pyproject.toml` (setuptools)
*   **Gözlemlenebilirlik:** Prometheus metrikleri ve `structlog` ile yapılandırılmış loglama.

## 🔌 API Etkileşimleri

*   **Gelen (Sunucu):**
    *   `sentiric-agent-service` (REST/JSON): `/transcribe` endpoint'ine ses dosyaları gönderir.

## 🚀 Yerel Geliştirme ve Test

1.  **Sanal Ortam Oluşturun:** `python -m venv .venv && source .venv/bin/activate`
2.  **Bağımlılıkları Kurun:** `pip install -e ".[dev]"`
3.  **Servisi Başlatın:** `uvicorn app.main:app --reload --port 5001`
4.  **Testleri Çalıştırın:** `pytest -v`

## 🤝 Katkıda Bulunma

Katkılarınızı bekliyoruz! Lütfen projenin ana [Sentiric Governance](https://github.com/sentiric/sentiric-governance) reposundaki kodlama standartlarına ve katkıda bulunma rehberine göz atın.

---
## 🏛️ Anayasal Konum

Bu servis, [Sentiric Anayasası'nın (v11.0)](https://github.com/sentiric/sentiric-governance/blob/main/docs/blueprint/Architecture-Overview.md) **Zeka & Orkestrasyon Katmanı**'nda yer alan merkezi bir bileşendir.