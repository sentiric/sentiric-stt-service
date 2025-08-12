# 🎤 Sentiric STT Service - API Kullanım ve Demo Rehberi

Bu belge, çalışan `sentiric-stt-service`'in performansını ve doğruluğunu test etmek için pratik örnekler sunar.

## Önkoşullar

*   Servis, `docker compose` ile veya yerel `uvicorn` komutuyla çalışır durumda olmalıdır.
*   Test için `curl` gibi bir aracınız ve birkaç örnek `.wav` dosyanız olmalıdır.

---

### **Test 1: Doğruluk (Accuracy) Testi**

*   **Amaç:** Net bir ses dosyasının ne kadar doğru bir şekilde metne çevrildiğini görmek.
*   **Hazırlık:** İçinde "Merhaba dünya, bu bir test mesajıdır." gibi net bir cümlenin olduğu `test_tr.wav` adında bir ses dosyası hazırlayın.
*   **Komut:**
    ```bash
    curl -X POST -F "audio_file=@path/to/test_tr.wav;type=audio/wav" http://localhost:5001/api/v1/transcribe
    ```
*   **Beklenen Sonuç:**
    ```json
    {
      "text": "Merhaba dünya, bu bir test mesajıdır."
    }
    ```
    Dönen metnin orijinal metne ne kadar yakın olduğunu kontrol edin.

### **Test 2: Performans (Hız) Testi**

*   **Amaç:** 60 saniyelik bir ses dosyasının ne kadar sürede işlendiğini ölçmek (Gerçek Zaman Faktörü - RTF).
*   **Hazırlık:** 60 saniye uzunluğunda bir konuşma içeren `long_test.wav` dosyası hazırlayın.
*   **Komut:**
    ```bash
    time curl -X POST -F "audio_file=@path/to/long_test.wav;type=audio/wav" http://localhost:5001/api/v1/transcribe
    ```
*   **Beklenen Sonuç:** `curl` komutunun tamamlanma süresi (örn: `real 0m12.345s`), ses dosyasının süresinden (60s) çok daha kısa olmalıdır. Bu, RTF'nin 1'den küçük olduğunu ve servisin gerçek zamanlı senaryolar için uygun olduğunu gösterir.