# ⚡ Sentiric STT Service - Geliştirme Yol Haritası (v4.0)

Bu belge, `stt-service`'in geliştirme görevlerini projenin genel fazlarına uygun olarak listeler.

---

### **FAZ 1 & 2: Çift Modlu Transkripsiyon (Mevcut Durum)**

**Amaç:** Hem kayıtlı dosyaları hem de gerçek zamanlı ses akışını yüksek doğruluk ve dayanıklılıkla metne çevirebilen, üretim kalitesinde bir servis oluşturmak.

-   [x] **Görev ID: STT-CORE-01 - Temel API ve Adaptör Mimarisi**
    -   **Durum:** ✅ **Tamamlandı**
    -   **Kabul Kriterleri:** `/transcribe` ve `/health` endpoint'leri çalışır durumda. `faster-whisper` adaptörü, `BaseSTTAdapter`'dan türetilmiştir.

-   [x] **Görev ID: STT-CORE-02 - Dayanıklı Dosya İşleme ve Test Arayüzü**
    -   **Durum:** ✅ **Tamamlandı**
    -   **Kabul Kriterleri:** Servis, `ffmpeg` kullanarak gelen tüm ses dosyalarını standart bir formata (16kHz mono PCM) dönüştürür. Kök (`/`) adreste, dosya yükleyerek test imkanı sunan bir HTML arayüzü mevcuttur.

-   [x] **Görev ID: STT-CORE-03 - Gerçek Zamanlı Akış (Streaming)**
    -   **Durum:** ✅ **Tamamlandı**
    -   **Kabul Kriterleri:** `/api/v1/transcribe-stream` WebSocket endpoint'i, gelen 16kHz PCM ses akışını kabul eder. `webrtcvad` ile sessizlik anlarını tespit ederek, konuşma bittiğinde nihai metni `{"type": "final", ...}` formatında istemciye gönderir. Test arayüzünde mikrofonla canlı test imkanı bulunur.

---

### **FAZ 3: Gelişmiş Özellikler ve Optimizasyon (Sıradaki Öncelikler)**

**Amaç:** Servisin performansını, doğruluğunu ve hata ayıklama yeteneklerini daha da ileriye taşımak.

-   [ ] **Görev ID: STT-009 - Gelişmiş Hata Ayıklama Modu**
    -   **Açıklama:** Belirli bir `trace_id` ile gelen isteklerde, işlenen ses dosyasının (öncesi/sonrası) ve transkripsiyon sonucunun güvenli bir depolama alanına (örn: MinIO/S3) kaydedilmesini sağlayan bir "debug" modu ekle.
    -   **Kabul Kriterleri:**
        -   [ ] `.env` dosyasına `STT_DEBUG_MODE=true` ve `STT_DEBUG_STORAGE_URI` gibi değişkenler eklenmeli.
        -   [ ] Debug modu aktifken, her transkripsiyon işlemi sonunda işlenen ses dosyası (standartlaştırılmış `.wav` formatında) ve metin sonucu (`.json` olarak) belirtilen URI'ye yüklenmeli.
        -   [ ] Yükleme işlemi, ana transkripsiyon sürecini yavaşlatmayacak şekilde asenkron olarak yapılmalıdır.

-   [ ] **Görev ID: STT-003 - `whisper.cpp` Adaptörü**
    -   **Açıklama:** `whisper.cpp` kütüphanesi için yeni bir adaptör oluştur. Bu, potansiyel olarak daha da yüksek performans ve daha düşük kaynak kullanımı sunabilir.
    -   **Kabul Kriterleri:**
        -   [ ] `WhisperCppAdapter` adında yeni bir adaptör sınıfı oluşturulmalı.
        -   [ ] Bu adaptör, `BaseSTTAdapter` arayüzünü tam olarak implemente etmeli.
        -   [ ] `.env` dosyasındaki `STT_SERVICE_ADAPTER` değişkeni `whisper_cpp` olarak ayarlandığında, servisin bu adaptörü kullanarak çalışması sağlanmalı.
        -   [ ] Yeni adaptörün performansı, `faster-whisper` ile karşılaştırmalı olarak belgelenmeli.

-   [ ] **Görev ID: STT-004 - Bulut STT Adaptörü (örn: Google Speech-to-Text)**
    -   **Açıklama:** En yüksek doğruluk gerektiren senaryolar için Google Cloud'un STT API'sini kullanan bir adaptör oluştur.
    -   **Kabul Kriterleri:**
        -   [ ] `GoogleSttAdapter` adında yeni bir adaptör sınıfı oluşturulmalı.
        -   [ ] Adaptör, hem dosya tabanlı hem de streaming API'lerini desteklemelidir.
        -   [ ] `.env` dosyasından `STT_SERVICE_ADAPTER=google_stt` ayarı ile aktif hale getirilebilmelidir.