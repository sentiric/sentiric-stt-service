import structlog
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import Optional
from app.services.stt_service import transcribe_audio

router = APIRouter()
log = structlog.get_logger(__name__)

class TranscriptionResponse(BaseModel):
    text: str

@router.post("/transcribe", response_model=TranscriptionResponse, tags=["Speech-to-Text"])
async def create_transcription(
    language: Optional[str] = Form(None), 
    audio_file: UploadFile = File(...)
):
    if not (audio_file.content_type and audio_file.content_type.startswith("audio/")):
        log.warning(
            "Invalid file type received", 
            filename=audio_file.filename, 
            content_type=audio_file.content_type
        )
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")
    
    try:
        audio_bytes = await audio_file.read()
        
        log.info("Transcription request received", filename=audio_file.filename, language=language or "auto", size_kb=round(len(audio_bytes) / 1024, 2))
        
        result_text = transcribe_audio(audio_bytes, language)
        
        log.info("Transcription successful", text_length=len(result_text))
        return {"text": result_text}

    except Exception as e:
        log.error("Error during transcription", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing the audio file.")