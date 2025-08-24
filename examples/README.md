# Örnek Uygulama: Simüle Edilmiş Telefon Görüşmesi (G.711 Kalitesi)

Bu dizin, `stt-service`'in gerçek zamanlı transkripsiyon yeteneklerini, **düşük kaliteli bir telefon görüşmesini (8000 Hz)** simüle ederek test etmek için pratik bir Python script'i içerir.

Bu uygulama, `sentiric-media-service`'in yapacağı temel ses işleme görevini tam olarak taklit eder:
1.  Mikrofondan sesi telefon kalitesinde (`8000 Hz`) yakalar.
2.  Bu sesi, `stt-service`'in beklediği standart formata (`16000 Hz`) **kendi içinde** dönüştürür.
3.  Bu standartlaştırılmış sesi, WebSocket üzerinden anlık olarak `stt-service`'e gönderir.
4.  `stt-service`'ten gelen transkripsiyon sonuçlarını konsola yazdırır.

Bu demo, `stt-service`'in temiz bir `16kHz` akış aldığında ne kadar iyi çalıştığını ve bir `media-service`'in format dönüşümünün neden önemli olduğunu gösterir.

## Kurulum

1.  Bu örnek, Python 3.10+ gerektirir.
2.  Yeni bir sanal ortam oluşturun ve `requirements.txt` dosyasını kurun:
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

## Çalıştırma

1.  `sentiric-stt-service`'in Docker üzerinde çalıştığından emin olun.
2.  Aşağıdaki komutla simülasyonu başlatın:
    ```bash
    python g711_test.py
    ```
3.  Konuşmaya başlayın. Transkripsiyon sonuçlarını terminalde göreceksiniz.