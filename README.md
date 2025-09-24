# ⚡ Sentiric STT Service (Speech-to-Text)

[![Status](https://img.shields.io/badge/status-production_ready-success.svg)]()
[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![Model](https://img.shields.io/badge/model-medium-blue.svg)]()

**Sentiric STT Service**, Sentiric "İletişim İşletim Sistemi" ekosisteminin "kulakları" olarak görev yapan, yüksek performanslı ve dayanıklı bir yapay zeka servisidir. Temel amacı, iki ana senaryoda ses verisini yüksek doğrulukla metne dönüştürmektir: **kayıtlı ses dosyaları** ve **gerçek zamanlı ses akışları.**

Bu servis, "en küçük sistemde en yüksek performans" hedefiyle tasarlanmış olup, minimum kaynak tüketimiyle (CPU üzerinde `medium` model) canlı telefon görüşmeleri gibi zorlu senaryoları destekleyecek şekilde optimize edilmiştir.

---

## 🏛️ Servis Sorumlulukları ve Felsefesi

Bu servisin mimarisi, "Tek Sorumluluk Prensibi" üzerine kuruludur.

1.  **Uzmanlık Alanı:** Servisin tek ve ana görevi, kendisine verilen **temiz ve standart formattaki** ses verisini en yüksek doğrulukla metne çevirmektir.
2.  **Format Esnekliği (Dosya Yükleme):** Farklı formatlardaki (`.mp3`, `.m4a`, `.ogg` vb.) ses dosyalarını kabul eder ve bunları transkripsiyon öncesi **kendi içinde standart formata (`16kHz PCM WAV`) dönüştürür.** Bu senaryoda bir "Ağ Geçidi" görevi görür.
3.  **Performans Odaklılık (Gerçek Zamanlı Akış):** Canlı görüşmeler gibi gecikmenin kritik olduğu senaryolarda, sesi gönderen istemcinin (`media-service` gibi) sesi standart format olan **`16kHz, 16-bit, mono PCM`** olarak göndermesini bekler. Bu, gereksiz format dönüşümünü ortadan kaldırarak maksimum performans sağlar.

---

## 🎯 Temel Yetenekler

*   **Çift Modlu Çalışma:** Hem asenkron dosya yüklemeleri (`/transcribe`) hem de anlık görüşmeler için gerçek zamanlı WebSocket akışını (`/transcribe-stream`) destekler.
*   **Yüksek Doğruluk:** `faster-whisper` (CTranslate2) motoru ve varsayılan olarak `medium` modeli sayesinde, özellikle Türkçe gibi dillerde yüksek doğrulukta transkripsiyon sağlar.
*   **Akıllı Filtreleme:** Modelin "halüsinasyonlarını" (anlamsız metinler üretmesini) ve ortam gürültüsünü, olasılık tabanlı filtreler kullanarak akıllıca ayıklar.
*   **Otomatik Dil Tespiti:** Dil belirtilmediğinde, gelen sesin dilini otomatik olarak algılar.
*   **Dayanıklılık:** `ffmpeg` entegrasyonu sayesinde, bozuk veya standart dışı ses dosyalarını bile işleyebilir.
*   **İnteraktif Test ve Ayar:** Servis, canlı olarak filtre eşiklerini değiştirerek en iyi doğruluk ayarlarını bulmanızı sağlayan bir web arayüzü (`/`) sunar.

---

## 🔌 API Entegrasyon Rehberi

Bu servisi kullanmak isteyen diğer servisler (`agent-service`, `media-service` vb.) için entegrasyon yöntemleri aşağıda açıklanmıştır.

### **Senaryo 1: Kayıtlı Bir Ses Dosyasını Metne Çevirme**

Bir toplantı kaydı, sesli mesaj veya arşivlenmiş bir telefon görüşmesi gibi tamamlanmış bir ses dosyasını metne çevirmek için bu yöntemi kullanın.

*   **Endpoint:** `POST /api/v1/transcribe`
*   **Method:** `POST`
*   **Gövde Tipi:** `multipart/form-data`
*   **Beklenen Girdi:**
    *   `audio_file`: Ses dosyası (`.mp3`, `.wav`, `.m4a`, `.ogg`, vb. herhangi bir format).
    *   `language` (isteğe bağlı): `tr`, `en` gibi bir dil kodu. Gönderilmezse, dil otomatik algılanır.
    *   `logprob_threshold` (isteğe bağlı): Filtre eşiği. Varsayılan (`-1.0`) kullanılır.
    *   `no_speech_threshold` (isteğe bağlı): Filtre eşiği. Varsayılan (`0.75`) kullanılır.
*   **Başarılı Çıktı (`200 OK`):**
    ```json
    {
      "text": "Transkripsiyon sonucu olan metin buraya gelecek."
    }
    ```

### **Senaryo 2: Gerçek Zamanlı Ses Akışını Metne Çevirme**

Canlı bir telefon görüşmesi, bir web arayüzündeki mikrofon girişi veya `media-service`'ten gelen anlık ses akışı için bu yöntemi kullanın.

*   **Endpoint:** `WS /api/v1/transcribe-stream`
*   **Protokol:** `WebSocket`
*   **URL Parametreleri (isteğe bağlı):**
    *   `?language=tr`
    *   `?logprob_threshold=-1.0`
    *   `?no_speech_threshold=0.75`
*   **Beklenen Girdi (İstemciden Sunucuya):**
    *   Sürekli bir **binary** mesaj akışı.
    *   Ses formatı **MUTLAKA** `16kHz, 16-bit, mono, ham PCM` olmalıdır.
*   **Başarılı Çıktı (Sunucudan İstemciye):**
    *   Konuşma bittiğinde ve bir sessizlik algılandığında gönderilen JSON mesajları:
    ```json
    {
      "type": "final",
      "text": "Kullanıcının o an söylediği cümlenin çevirisi."
    }
    ```
*   **Hata Durumu Çıktısı:**
    ```json
    {
      "type": "error",
      "message": "Bir hata oluştu."
    }
    ```

---

## 🚀 Yerel Geliştirme

1.  **Bağımlılıkları Yükleyin:**
2.  **Ortam Değişkenlerini Ayarlayın:** `.env.example` dosyasını `.env` olarak kopyalayın ve gerekli değişkenleri doldurun.
3.  **Servisi Çalıştırın:**

---
## 🏛️ Anayasal Konum

Bu servis, [Sentiric Anayasası'nın (v11.0)](https://github.com/sentiric/sentiric-governance/blob/main/docs/blueprint/Architecture-Overview.md) **Zeka & Orkestrasyon Katmanı**'nda yer alan merkezi bir bileşendir.