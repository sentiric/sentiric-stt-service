# ⚡ Sentiric STT Service - Görev Listesi

Bu belge, `stt-service`'in geliştirme yol haritasını ve önceliklerini tanımlar.

---

### Faz 1: Yüksek Performanslı ve Dayanıklı Dosya Tabanlı Transkripsiyon (Tamamlandı)

Bu faz, servisin ses dosyalarını verimli, doğru ve format fark etmeksizin dayanıklı bir şekilde metne çevirmesini hedefler.

-   [x] **FastAPI Sunucusu:** `/api/v1/transcribe` ve `/health` endpoint'leri.
-   [x] **Adaptör Mimarisi:** Farklı STT motorlarını desteklemek için `BaseSTTAdapter` soyut sınıfı ve `stt_service.py`'deki kayıt mekanizması.
-   [x] **Faster-Whisper Adaptörü:** `faster-whisper` kütüphanesini kullanarak yüksek performanslı CPU tabanlı transkripsiyon.
-   [x] **Optimize Edilmiş Dockerfile:** Modelleri build sırasında indiren ve son imajı hafif tutan multi-stage `Dockerfile`.
-   [x] **Otomatize Testler:** `pytest` ile temel API endpoint'lerinin ve dosya tipi kontrolünün test edilmesi.
-   [x] **Görev ID: STT-005 - Dayanıklı Ses İşleme:** Servise gelen tüm ses dosyalarını, modele göndermeden önce standart bir formata (16kHz mono, 16-bit PCM) dönüştüren `ffmpeg` tabanlı bir ön işleme katmanı eklendi.
-   [x] **Görev ID: STT-006 - Gelişmiş Test Arayüzü (Dosya):** Servisin kök adresinde, dosya yükleme ve dil seçimi özelliklerine sahip, kullanımı kolay bir HTML/JS test arayüzü oluşturuldu.
-   [x] **Görev ID: STT-007 - Birleşik Loglama:** Uvicorn ve Structlog logları birleştirilerek, tüm sistem çıktısının tek, tutarlı ve profesyonel bir formatta olması sağlandı.

---

### Faz 2: Gerçek Zamanlı Akış (Streaming) Desteği (Tamamlandı)

Bu faz, servisi gerçek zamanlı diyaloglar için uygun hale getirecek olan "streaming" yeteneğini eklemeyi hedefler.

-   [x] **Görev ID: STT-001 - WebSocket Endpoint'i:** FastAPI'ye `/api/v1/transcribe-stream` adında bir WebSocket endpoint'i eklendi. Bu endpoint, istemciden gelen anlık ses verisi akışını (16kHz, 16-bit PCM) kabul eder.
-   [x] **Görev ID: STT-002 - Akışlı Transkripsiyon Mantığı:** Ses akışını anlık olarak işleyen, `webrtcvad` ile ses aktivitesini (VAD) algılayarak sessizlik anlarında metin bloğunu sonuçlandıran ve sonucu WebSocket üzerinden `{"type": "final", "text": "..."}` formatında geri gönderen bir `AudioProcessor` sınıfı oluşturuldu.
-   [x] **Görev ID: STT-008 - Gerçek Zamanlı Test Arayüzü (Mikrofon):** Mevcut test arayüzüne, tarayıcı mikrofonundan ses alıp WebSocket endpoint'ine anlık olarak gönderen ve dönen transkripsiyon sonuçlarını gösteren yeni bir "Gerçek Zamanlı" sekmesi eklendi.

---

### Faz 3: Gelişmiş Özellikler ve Diğer Adaptörler (Sıradaki Öncelikler)

-   [ ] **Görev ID: STT-003 - `whisper.cpp` Adaptörü**
    -   **Açıklama:** `whisper.cpp` kütüphanesi için yeni bir adaptör oluştur. Bu, potansiyel olarak daha da yüksek performans ve daha düşük kaynak kullanımı sunabilir.
    -   **Durum:** ⬜ Planlandı.

-   [ ] **Görev ID: STT-004 - Bulut STT Adaptörü (örn: Google Speech-to-Text)**
    -   **Açıklama:** En yüksek doğruluk gerektiren senaryolar için Google Cloud'un STT API'sini kullanan bir adaptör oluştur.
    -   **Durum:** ⬜ Planlandı.

-   [ ] **Görev ID: STT-009 - Gelişmiş Hata Ayıklama Modu**
    -   **Açıklama:** Belirli bir `trace_id` ile gelen isteklerde, işlenen ses dosyasının (öncesi/sonrası) ve transkripsiyon sonucunun güvenli bir depolama alanına (örn: MinIO/S3) kaydedilmesini sağlayan bir "debug" modu ekle. Bu, canlıdaki sorunları analiz etmek için kritik olacaktır.
    -   **Durum:** ⬜ Planlandı.