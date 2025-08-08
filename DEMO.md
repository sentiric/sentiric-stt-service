### **FAZ 3: Gerçek Testler, Performans Analizi ve Demo**

Otomatik testler "kodun doğru çalıştığını" söyler. Gerçek testler "ürünün doğru çalıştığını" gösterir.

**Test Ortamı:**
*   Servis, `docker compose` ile çalışır durumda.
*   Test için `curl` veya `Postman` gibi bir araç kullanacağız.
*   Farklı türde ses dosyaları hazırlayacağız:
    1.  `docs/audio/speakers/tr/default_male.wav`: Türkçe, stüdyo kalitesinde, net bir konuşma.
    2.  `docs/audio/speakers/en/default_male.wav`: İngilizce, arkada gürültü olan bir konuşma.
    3.  `docs/audio/speakers/tr/default_male.wav`: Türkçe, 1-2 dakikalık uzun bir konuşma.

**Test 1: Doğruluk (Accuracy) Testi**
*   **Amaç:** `docs/audio/speakers/tr/default_male.wav` dosyasını servise gönderip dönen metnin orijinal metne ne kadar yakın olduğunu ölçmek.
*   **Komut:**
    ```bash
    curl -X POST -F "audio_file=@docs/audio/speakers/tr/test.wav;type=audio/wav" http://localhost:5001/api/v1/transcribe
    ```
*   **Başarı Kriteri:** Dönen metnin Kelime Hata Oranı (Word Error Rate - WER) %10'un altında olmalı.

**Test 2: Gürültüye Dayanıklılık Testi**
*   **Amaç:** `docs/audio/speakers/en/default_male.wav` dosyasını göndererek modelin zorlu koşullardaki performansını görmek.
*   **Komut:**
    ```bash
    curl -X POST -F "audio_file=@docs/audio/speakers/en/test.wav;type=audio/wav" http://localhost:5001/api/v1/transcribe
    ```
*   **Başarı Kriteri:** Anlamın büyük ölçüde korunması.

**Test 3: Performans (Hız) Testi**
*   **Amaç:** `docs/audio/speakers/tr/default_male.wav` (örneğin 60 saniyelik bir dosya) gönderip, yanıtın ne kadar sürede geldiğini ölçmek. Buna **Gerçek Zaman Faktörü (Real-Time Factor - RTF)** denir.
*   **Komut:**
    ```bash
    time curl -X POST -F "audio_file=@docs/audio/speakers/tr/default_male.wav;type=audio/wav" http://localhost:5001/api/v1/transcribe
    ```
*   **Başarı Kriteri:** İşlem süresi, ses dosyasının süresinden önemli ölçüde daha kısa olmalı (RTF < 1.0). Örneğin, 60 saniyelik bir ses 10-15 saniyede işleniyorsa, bu harika bir sonuçtur.

Bu gerçek testler, servisin sadece kağıt üzerinde değil, pratik uygulamada da ne kadar güçlü ve güvenilir olduğunu bize gösterecektir.