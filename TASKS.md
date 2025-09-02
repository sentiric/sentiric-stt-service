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