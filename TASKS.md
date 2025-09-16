# ⚡ Sentiric STT Service - Görev Listesi (v4.1 - Dayanıklılık)

Bu belge, `stt-service`'in diyalog döngüsündeki kritik rolünü daha sağlam bir şekilde yerine getirmesi için gereken görevleri tanımlar.

---

### **FAZ 1 : Çift Modlu Transkripsiyon (Tamamlanmış Görevler)**
*   [x] **STT-CORE-01**: Temel API ve Adaptör Mimarisi
*   [x] **STT-CORE-02**: Dayanıklı Dosya İşleme ve Test Arayüzü
*   [x] **STT-CORE-03**: Gerçek Zamanlı Akış (Streaming)

---

### **FAZ 2: Dayanıklılık ve Akıllı Hata Yönetimi (Mevcut Odak)**

-   **Görev ID: STT-BUG-01 - WebSocket Sessizlik/Timeout Yönetimi**
    -   **Durum:** ✅ **Tamamlandı**
    -   **Öncelik:** **KRİTİK**
    -   **Stratejik Önem:** `agent-service`'in hatalı bir "anlayamadım" döngüsüne girmesini ve çağrıları erken sonlandırmasını engeller.
    -   **Problem Tanımı:** Gerçek zamanlı akış sırasında kullanıcı hiç konuşmadığında, `stt-service` bağlantıyı açık tutuyor ancak `agent-service`'e herhangi bir bildirim göndermiyordu.
    -   **Çözüm Stratejisi:** `AudioProcessor` sınıfına, belirli bir süre (10sn) ses paketi gelmediğinde istemciye `{"type": "no_speech_timeout"}` mesajı gönderen bir zamanlayıcı eklendi.
    -   **Kabul Kriterleri:**
        -   [x] Bir WebSocket bağlantısı kurulduktan sonra 10 saniye boyunca hiç ses gönderilmezse, `stt-service` istemciye `no_speech_timeout` tipinde bir JSON mesajı göndermelidir.
        -   [x] `agent-service`, bu mesajı alarak "Sizi duyamıyorum" anonsu çalabilmelidir.
    -   **Tahmini Süre:** ~2-3 Saat

---

### **FAZ 3: Gelişmiş Özellikler ve Optimizasyon (Sıradaki Öncelikler)**

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

### **FAZ 4: Gözlemlenebilirlik ve Operasyon (Sıradaki Öncelik)**

-   **Görev ID: LLM-OPS-01 - "Sessiz" Sağlık Kontrolü Endpoint'i Ekle**
    -   **Durum:** ⬜ **Yapılacak (Öncelik 1 - ORTA)**
    -   **Bağımlılık:** `infrastructure`'daki `OPS-IMPRV-01`
    -   **Açıklama:** Docker `healthcheck` mekanizmasının neden olduğu log kirliliğini önlemek için, log basmayan yeni bir `/healthz` endpoint'i oluşturulmalıdır. Loglama middleware'i bu endpoint'e yapılan istekleri atlayacak şekilde güncellenmelidir.
    -   **Kabul Kriterleri:**
        -   [ ] `/healthz` adında yeni bir endpoint oluşturulmalı.
        -   [ ] Bu endpoint, loglama middleware'i tarafından filtrelenmeli ve çağrıldığında konsola hiçbir log basmamalıdır.
        -   [ ] Endpoint, `200 OK` durum koduyla boş bir yanıt dönmelidir.    