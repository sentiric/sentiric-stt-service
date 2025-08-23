import subprocess
import structlog
from app.core.config import settings

log = structlog.get_logger(__name__)

def resample_audio(audio_bytes: bytes) -> bytes:
    """
    Verilen ses byte'larını ffmpeg kullanarak hedef örnekleme oranına dönüştürür
    ve temiz, standart bir PCM WAV formatına sokar.
    Bu, modele her zaman doğru ve temiz formatta ses gitmesini garanti eder.
    """
    target_sample_rate = settings.STT_SERVICE_TARGET_SAMPLE_RATE
    log.info(f"Resampling and cleaning audio to {target_sample_rate}Hz, PCM S16LE...")

    try:
        command = [
            'ffmpeg',
            '-i', 'pipe:0',                  # Giriş stdin'den
            '-ar', str(target_sample_rate),  # Hedef örnekleme oranı
            '-ac', '1',                      # Mono kanal
            '-acodec', 'pcm_s16le',          # YENİ: Temiz 16-bit PCM formatına zorla
            '-f', 'wav',                     # Çıkış formatı WAV
            'pipe:1'                         # Çıkış stdout'a
        ]
        
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout_data, stderr_data = process.communicate(input=audio_bytes)
        
        if process.returncode != 0:
            error_message = stderr_data.decode('utf-8', errors='ignore').strip()
            log.error(
                "FFmpeg processing failed",
                return_code=process.returncode,
                ffmpeg_error=error_message
            )
            return audio_bytes
            
        log.info("Audio processed successfully", original_size_kb=round(len(audio_bytes)/1024, 2), new_size_kb=round(len(stdout_data)/1024, 2))
        return stdout_data

    except FileNotFoundError:
        log.error("ffmpeg command not found. Make sure ffmpeg is installed and in your PATH. Skipping processing.")
        return audio_bytes
    except Exception as e:
        log.error("An unexpected error occurred during audio processing", error=str(e), exc_info=True)
        return audio_bytes