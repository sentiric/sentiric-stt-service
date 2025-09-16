# ⚡ Sentiric STT Service - Görev Listesi (v4.1 - Dayanıklılık)

Bu belge, `stt-service`'in diyalog döngüsündeki kritik rolünü daha sağlam bir şekilde yerine getirmesi için gereken görevleri tanımlar.

---


### **Gelecek fazlar: Gelişmiş Özellikler ve Optimizasyon (Sıradaki Öncelikler)**

-   [ ] **Görev ID: STT-009 - Gelişmiş Hata Ayıklama Modu**
    -   **Durum:** ⬜ **Planlandı**
    -   **Öncelik:** DÜŞÜK
    -   **Açıklama:** Belirli bir `trace_id` ile gelen isteklerde, işlenen ses dosyasının ve transkripsiyon sonucunun MinIO/S3'e kaydedilmesini sağlayan bir "debug" modu ekle.

-   [ ] **Görev ID: STT-REFACTOR-01 - Format Dönüşüm Sorumluluğunu Kaldırma**
    -   **Durum:** ⬜ **Planlandı**
    -   **Öncelik:** DÜŞÜK
    -   **Bağımlılık:** `MEDIA-REFACTOR-01`'in tamamlanmış olması.

**Amaç:** Servisi, farklı yapay zeka sağlayıcılarını "tak-çıkar" mantığıyla kullanabilecek bir yapıya kavuşturmak ve gelecekteki "STT Gateway" mimarisine zemin hazırlamak.

-   **Görev ID: STT-ADAPT-01 - Google Live API Adaptörü Entegrasyonu**
    -   **Durum:** ⬜ **Yapılacak**
    -   **Öncelik:** YÜKSEK
    -   **Stratejik Önem:** Platformun, endüstri lideri bir STT motorunu `faster-whisper`'a bir alternatif olarak kullanabilmesini sağlar. Bu, doğruluk, hız ve maliyet optimizasyonu için kritik bir esneklik katmanıdır.
    -   **Kabul Kriterleri:**
        -   [ ] `google-generativeai` kütüphanesi `pyproject.toml`'a eklenmeli.
        -   [ ] `app/services/adapters/` altına `google_live_adapter.py` dosyası oluşturulmalı ve `BaseSTTAdapter` arayüzünü implemente etmeli.
        -   [ ] Adaptör, başlangıçta `settings.GOOGLE_API_KEY` ve `STT_SERVICE_GOOGLE_MODEL_NAME` değişkenlerini kullanarak Google'ın modelini yüklemeli.
        -   [ ] `app/services/stt_service.py` içinde yeni adaptör, `"google_live"` anahtarıyla kaydedilmeli.
        -   [ ] `stt-service.env` dosyasında `STT_SERVICE_ADAPTER="google_live"` olarak ayarlandığında, servisin `/health` endpoint'i ve logları Google modelinin yüklendiğini doğrulamalıdır.

-   **Görev ID: STT-REFACTOR-02 - STT Gateway Mimarisine Geçiş (Vizyon)**
    -   **Durum:** ⬜ **Planlandı**
    -   **Öncelik:** DÜŞÜK
    -   **Açıklama:** Bu servisin sorumluluğunu sadece `faster-whisper` modelini çalıştırmakla sınırlamak (`stt-whisper-service` olarak yeniden adlandırmak) ve API yönlendirme, WebSocket yönetimi gibi görevleri yeni oluşturulacak bir `stt-gateway-service`'e devretmek. Bu, `tts-gateway` mimarisinin başarısını STT katmanına taşır.
    -   **Bağımlılık:** `STT-ADAPT-01`'in tamamlanması, bu mimarinin gerekliliğini ve faydalarını daha net ortaya koyacaktır.
