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
    if not audio_file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="Geçersiz dosya tipi. Lütfen bir ses dosyası yükleyin.")
    
    try:
        # Dosyanın içeriğini byte olarak oku
        audio_bytes = await audio_file.read()
        
        logger.info("Transkripsiyon talebi alındı", filename=audio_file.filename, content_type=audio_file.content_type)
        
        # STT servisine gönder
        result_text = transcribe_audio(audio_bytes)
        
        logger.info("Transkripsiyon başarılı", text=result_text)
        return {"text": result_text}

    except Exception as e:
        logger.error("Transkripsiyon sırasında hata oluştu", error=str(e))
        raise HTTPException(status_code=500, detail="Ses dosyası işlenirken bir hata oluştu.")