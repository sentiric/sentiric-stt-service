from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import Optional
from app.services.stt_service import transcribe_audio
from app.core.logging import logger

router = APIRouter()

class TranscriptionResponse(BaseModel):
    text: str

@router.post("/transcribe", response_model=TranscriptionResponse, tags=["Speech-to-Text"])
async def create_transcription(
    # DÜZELTME: Artık language parametresini de form verisi olarak alıyoruz.
    language: Optional[str] = Form(None), 
    audio_file: UploadFile = File(...)
):
    """
    Yüklenen bir ses dosyasını metne çevirir.
    Opsiyonel 'language' parametresi ile dil belirtilebilir.
    """
    is_audio = audio_file.content_type and audio_file.content_type.startswith("audio/")
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
        
        logger.info("Transkripsiyon talebi alındı", filename=audio_file.filename, language=language)
        
        # DÜZELTME: Dil bilgisini `transcribe_audio` fonksiyonuna iletiyoruz.
        result_text = transcribe_audio(audio_bytes, language)
        
        logger.info("Transkripsiyon başarılı", text=result_text)
        return {"text": result_text}

    except Exception as e:
        logger.error("Transkripsiyon sırasında hata oluştu", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ses dosyası işlenirken bir hata oluştu.")