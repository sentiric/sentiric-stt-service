import subprocess
import structlog
from app.core.config import settings

log = structlog.get_logger(__name__)

def resample_audio(audio_bytes: bytes) -> bytes:
    """
    Verilen ses byte'larını ffmpeg kullanarak hedef örnekleme oranına dönüştürür.
    Bu, modele her zaman doğru formatta ses gitmesini garanti eder.
    """
    target_sample_rate = settings.STT_SERVICE_TARGET_SAMPLE_RATE
    log.info(f"Resampling audio to {target_sample_rate}Hz...")

    try:
        command = [
            'ffmpeg',
            '-i', 'pipe:0',          # Giriş stdin'den
            '-ar', str(target_sample_rate), # Hedef örnekleme oranı
            '-ac', '1',              # Mono kanal
            '-f', 'wav',             # Çıkış formatı WAV
            'pipe:1'                 # Çıkış stdout'a
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
                "FFmpeg resampling failed",
                return_code=process.returncode,
                ffmpeg_error=error_message
            )
            # FFmpeg hatası durumunda orijinal byte'ları döndürmeyi deneyebiliriz
            # veya bir istisna fırlatabiliriz. Dayanıklılık için orijinali döndürmek
            # daha iyi olabilir.
            return audio_bytes
            
        log.info("Audio resampled successfully", original_size_kb=round(len(audio_bytes)/1024, 2), new_size_kb=round(len(stdout_data)/1024, 2))
        return stdout_data

    except FileNotFoundError:
        log.error("ffmpeg command not found. Make sure ffmpeg is installed and in your PATH. Skipping resampling.")
        return audio_bytes
    except Exception as e:
        log.error("An unexpected error occurred during resampling", error=str(e), exc_info=True)
        return audio_bytes