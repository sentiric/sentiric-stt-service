# ⚡ Sentiric STT Service - Görev Listesi

Bu belge, `stt-service`'in geliştirme yol haritasını ve önceliklerini tanımlar.

---

### Faz 1: Yüksek Performanslı Dosya Tabanlı Transkripsiyon (Mevcut Durum)

Bu faz, servisin ses dosyalarını verimli ve doğru bir şekilde metne çevirmesini hedefler.

-   [x] **FastAPI Sunucusu:** `/api/v1/transcribe` ve `/health` endpoint'leri.
-   [x] **Adaptör Mimarisi:** Farklı STT motorlarını desteklemek için `BaseSTTAdapter` soyut sınıfı ve `stt_service.py`'deki kayıt mekanizması.
-   [x] **Faster-Whisper Adaptörü:** `faster-whisper` kütüphanesini kullanarak yüksek performanslı CPU tabanlı transkripsiyon.
-   [x] **Optimize Edilmiş Dockerfile:** Modelleri build sırasında indiren ve son imajı hafif tutan multi-stage `Dockerfile`.
-   [x] **Otomatize Testler:** `pytest` ile temel API endpoint'lerinin ve dosya tipi kontrolünün test edilmesi.

---

### Faz 2: Gerçek Zamanlı Akış (Streaming) Desteği (Sıradaki Öncelik)

Bu faz, servisi gerçek zamanlı diyaloglar için uygun hale getirecek olan "streaming" yeteneğini eklemeyi hedefler.

-   [ ] **Görev ID: STT-001 - WebSocket Endpoint'i**
    -   **Açıklama:** FastAPI'ye `/api/v1/transcribe-stream` adında bir WebSocket endpoint'i ekle. Bu endpoint, istemciden gelen ses verisi akışını kabul etmelidir.
    -   **Durum:** ⬜ Planlandı.

-   [ ] **Görev ID: STT-002 - Akışlı Transkripsiyon Mantığı**
    -   **Açıklama:** `faster-whisper`'ın (veya bu iş için daha uygun başka bir kütüphanenin) akışlı (streaming) transkripsiyon yeteneğini kullanarak, gelen ses verisini anlık olarak metne çevirip WebSocket üzerinden geri gönder. "VAD (Voice Activity Detection)" filtresi ile sessizlik anlarında metin bloğunu sonuçlandır.
    -   **Durum:** ⬜ Planlandı.

---

### Faz 3: Gelişmiş Özellikler ve Diğer Adaptörler

-   [ ] **Görev ID: STT-003 - `whisper.cpp` Adaptörü**
    -   **Açıklama:** `whisper.cpp` kütüphanesi için yeni bir adaptör oluştur. Bu, potansiyel olarak daha da yüksek performans ve daha düşük kaynak kullanımı sunabilir.
    -   **Durum:** ⬜ Planlandı.

-   [ ] **Görev ID: STT-004 - Bulut STT Adaptörü (örn: Google Speech-to-Text)**
    -   **Açıklama:** En yüksek doğruluk gerektiren senaryolar için Google Cloud'un STT API'sini kullanan bir adaptör oluştur.
    -   **Durum:** ⬜ Planlandı.