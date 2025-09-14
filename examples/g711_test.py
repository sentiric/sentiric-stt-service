import asyncio
import websockets
import json
import pyaudio
import numpy as np
import audioop
import argparse
import logging
from typing import Optional

# Loglamayı yapılandır
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("G711_Simulator")

# --- Yapılandırma ---
STT_HOST = "localhost:15010"
INPUT_RATE = 8000
TARGET_RATE = 16000
CHUNK_SIZE = 800  # 100ms @ 8kHz (8000 * 0.100)

async def test_g711_simulation(language: str, logprob: Optional[float], nospeech: Optional[float]):
    """
    Mikrofondan 8kHz (telefon kalitesi) ses alır, 16kHz'e dönüştürür ve
    STT servisine anlık olarak gönderir.
    """
    
    # WebSocket URL'ini komut satırı argümanlarına göre dinamik olarak oluştur
    params = {
        'language': language,
        'logprob_threshold': logprob,
        'no_speech_threshold': nospeech
    }
    # Sadece değeri olan parametreleri URL'e ekle
    query_string = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
    websocket_url = f"ws://{STT_HOST}/api/v1/transcribe-stream?{query_string}"
    
    logger.info(f"🔌 STT Servisine bağlanılıyor: {websocket_url}")

    try:
        async with websockets.connect(websocket_url) as websocket:
            logger.info("✅ WebSocket bağlantısı başarıyla kuruldu.")
            
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=INPUT_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            
            logger.info("🎤 Telefon kalitesinde (8kHz) konuşmaya başlayın (Durdurmak için CTRL+C)...")
            logger.info("📞 Script, sesi 16kHz'e dönüştürüp STT servisine anlık olarak gönderiyor.")
            
            # Sunucudan gelen mesajları dinlemek için ayrı bir görev (task) başlat
            listen_task = asyncio.create_task(listen_for_transcripts(websocket))
            
            try:
                while True:
                    # 8000 Hz, 16-bit PCM ses verisini mikrofondan oku
                    data_8khz = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    
                    # Sesi 16000 Hz'e yeniden örnekle (resample)
                    data_16khz, _ = audioop.ratecv(data_8khz, 2, 1, INPUT_RATE, TARGET_RATE, None)
                    
                    # Standartlaştırılmış sesi WebSocket üzerinden sunucuya gönder
                    await websocket.send(data_16khz)
                        
            except KeyboardInterrupt:
                logger.info("\n⏹️ Kullanıcı tarafından durduruldu.")
                
            finally:
                # Kaynakları temiz bir şekilde kapat
                logger.info("Kaynaklar temizleniyor...")
                stream.stop_stream()
                stream.close()
                p.terminate()
                # Sunucuyu dinleme görevini iptal et
                listen_task.cancel()
                # WebSocket bağlantısını kapat
                await websocket.close()
                # Görevin tamamen sonlandığından emin ol
                await listen_task
                
    except asyncio.CancelledError:
        logger.info("Ana görev iptal edildi.")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.error(f"❌ Bağlantı hatası: Sunucu bağlantıyı reddetti veya kapattı. (Hata: {e})")
        logger.error("💡 İpucu: 'stt-service' konteynerinin çalıştığından emin misiniz?")
    except Exception as e:
        logger.error(f"❌ Beklenmedik bir hata oluştu: {e}")

async def listen_for_transcripts(websocket):
    """
    WebSocket'ten gelen transkripsiyon mesajlarını dinler ve konsola yazdırır.
    """
    try:
        async for message in websocket:
            try:
                result = json.loads(message)
                if result.get("type") == "final" and result.get("text"):
                    print(f"   ↳ [Transkript]: {result['text']}")
                elif result.get("type") == "error":
                     logger.error(f"Sunucudan hata mesajı alındı: {result.get('message')}")
            except json.JSONDecodeError:
                logger.warning(f"Sunucudan geçersiz JSON formatında mesaj alındı: {message}")
    except (websockets.exceptions.ConnectionClosed, asyncio.CancelledError):
        logger.info("👂 Sunucu dinleme görevi sonlandırıldı.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Simulated G.711 telephone call to Sentiric STT Service.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '-l', '--language', 
        type=str, 
        default='tr', 
        help='Language code for transcription (e.g., tr, en).\nVarsayılan: tr'
    )
    parser.add_argument(
        '-lp', '--logprob', 
        type=float, 
        default=-1.0, 
        help='Log probability threshold to filter hallucinations.\n(e.g., -1.0). Varsayılan olarak sunucu ayarı kullanılır.'
    )
    parser.add_argument(
        '-ns', '--nospeech', 
        type=float, 
        default=0.75, 
        help='No speech probability threshold to filter noise.\n(e.g., 0.75). Varsayılan olarak sunucu ayarı kullanılır.'
    )
    args = parser.parse_args()

    try:
        asyncio.run(test_g711_simulation(args.language, args.logprob, args.nospeech))
    except KeyboardInterrupt:
        print("\nProgramdan çıkılıyor.")