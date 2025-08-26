# ⚡ Sentiric STT Service - Mantık ve Akış Mimarisi

**Belge Amacı:** Bu doküman, `stt-service`'in Sentiric platformunun **"evrensel kulakları"** olarak stratejik rolünü, çift modlu çalışma prensibini ve `agent-service` ile `media-service` arasındaki kritik etkileşimini açıklar.

---

## 1. Stratejik Rol: "Evrensel Ses Çözücü"

Bu servisin tek görevi, kendisine herhangi bir formatta gelen ses verisini, platformun anlayabileceği tek bir şeye dönüştürmektir: **metin**. Servis, farklı senaryoların gerektirdiği farklı hız ve format ihtiyaçlarına cevap verebilecek şekilde tasarlanmıştır.

**Bu servis sayesinde platform:**
1.  **Her Şeyi Duyar:** `ffmpeg` entegrasyonu sayesinde, `.mp3`, `.m4a`, `.ogg` gibi onlarca farklı formattaki ses dosyasını işleyebilir. Bu, esneklik sağlar.
2.  **Anlık Konuşmayı Anlar:** Gerçek zamanlı telefon görüşmeleri gibi gecikmenin kritik olduğu senaryolar için optimize edilmiş WebSocket tabanlı bir akış (`streaming`) arayüzü sunar.
3.  **Akıllıca Filtreler:** `faster-whisper` modelinin gelişmiş VAD (Ses Aktivitesi Tespiti) ve olasılık filtrelerini kullanarak, telefon hattındaki gürültüleri veya modelin anlamsız "halüsinasyonlarını" ayıklayarak temiz bir metin çıktısı üretir.
4.  **Teknoloji Bağımsızdır:** Adaptör mimarisi sayesinde, yarın `faster-whisper` yerine `whisper.cpp` veya Google'ın STT servisini kullanmak, sadece bu servisin içinde bir konfigürasyon değişikliği gerektirir.

---

## 2. Uçtan Uca Akışlar

### Senaryo 1: Kayıtlı Bir Ses Dosyasının Metne Çevrilmesi (`/transcribe`)

Bu akış, daha az acil olan, tamamlanmış ses dosyaları içindir.

```mermaid
sequenceDiagram
    participant AgentService as Agent Service
    participant STTService as STT Service
    participant FFmpeg as FFmpeg (Dahili)
    participant Whisper as faster-whisper Modeli (Dahili)

    AgentService->>STTService: POST /api/v1/transcribe (audio_file=@call123.mp3)
    
    Note right of STTService: Gelen MP3 dosyasını alır.
    
    STTService->>FFmpeg: Sesi standart formata çevir <br> (16kHz, 16-bit mono PCM)
    FFmpeg-->>STTService: Ham ses verisi (bytes)
    
    Note right of STTService: Temizlenmiş sesi modele gönderir.

    STTService->>Whisper: transcribe(ham_ses_verisi)
    Whisper-->>STTService: Segmentler ve metin

    Note right of STTService: Sonuçları filtreler ve birleştirir.

    STTService-->>AgentService: 200 OK { text: "Merhaba, bu bir test..." }
```

### Senaryo 2: Gerçek Zamanlı Ses Akışının Metne Çevrilmesi (/transcribe-stream)
Bu akış, canlı telefon görüşmeleri için kritik öneme sahiptir.

```mermaid
sequenceDiagram
    participant MediaService as Media Service
    participant AgentService as Agent Service
    participant STTService as STT Service (WebSocket)
    participant Whisper as faster-whisper Modeli (Dahili)

    Note over MediaService, AgentService: Kullanıcı konuşuyor, RTP paketleri <br> Media Service'e ulaşıyor ve <br> Agent Service'e stream ediliyor.

    AgentService->>STTService: WebSocket Bağlantısı Kurar
    
    loop Her ses paketi için
        AgentService->>STTService: Ham PCM ses paketi gönderir (binary)
    end
    
    Note right of STTService: Ses paketlerini biriktirir. <br> VAD ile sessizlik anını tespit eder. <br> Biriken sesi modele gönderir.

    STTService->>Whisper: transcribe(biriken_ses_blogu)
    Whisper-->>STTService: Sonuç metni

    STTService-->>AgentService: JSON Mesajı: { "type": "final", "text": "..." }
```
