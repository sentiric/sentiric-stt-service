from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.services.stt_service import transcribe_audio
from app.core.logging import logger

router = APIRouter()

class TranscriptionResponse(BaseModel):
    text: str

@router.post("/transcribe", response_model=TranscriptionResponse, tags=["Speech-to-Text"])
async def create_transcription(audio_file: UploadFile = File(...)):
    """
    Yüklenen bir ses dosyasını metne çevirir.
    """
    # GÜÇLENDİRİLMİŞ KONTROL:
    # 1. Önce content_type'a bak
    is_audio = audio_file.content_type and audio_file.content_type.startswith("audio/")
    
    # 2. Eğer content_type yoksa veya uygun değilse, dosya adının uzantısına bak
    if not is_audio and audio_file.filename:
        allowed_extensions = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
        file_ext = "." + audio_file.filename.split('.')[-1].lower()
        if file_ext in allowed_extensions:
            is_audio = True

    if not is_audio:
        logger.warning(
            "Geçersiz dosya tipiyle transkripsiyon talebi reddedildi.", 
            filename=audio_file.filename, 
            content_type=audio_file.content_type
        )
        raise HTTPException(status_code=400, detail="Geçersiz dosya tipi. Lütfen bir ses dosyası (.wav, .mp3 vb.) yükleyin.")
    
    try:
        audio_bytes = await audio_file.read()
        
        logger.info("Transkripsiyon talebi alındı", filename=audio_file.filename, content_type=audio_file.content_type)
        
        result_text = transcribe_audio(audio_bytes)
        
        logger.info("Transkripsiyon başarılı", text=result_text)
        return {"text": result_text}

    except Exception as e:
        logger.error("Transkripsiyon sırasında hata oluştu", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Ses dosyası işlenirken bir hata oluştu.")