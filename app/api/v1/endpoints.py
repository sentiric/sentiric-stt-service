import structlog
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from app.services.stt_service import transcribe_audio
from app.utils.audio import resample_audio
from app.services.streaming_service import AudioProcessor # YENİ

router = APIRouter()
log = structlog.get_logger(__name__)

class TranscriptionResponse(BaseModel):
    text: str

# Mevcut dosya tabanlı endpoint aynı kalıyor...
@router.post("/transcribe", response_model=TranscriptionResponse, tags=["Speech-to-Text"])
async def create_transcription(
    language: Optional[str] = Form(None), 
    audio_file: UploadFile = File(...)
):
    # ... (kod değişmedi)

# YENİ: Gerçek zamanlı transkripsiyon için WebSocket endpoint'i
@router.websocket("/transcribe-stream")
async def websocket_transcription(websocket: WebSocket, language: Optional[str] = None):
    await websocket.accept()
    log.info("WebSocket connection established", client=websocket.client, language=language)
    
    audio_processor = AudioProcessor(language=language)

    async def audio_chunk_generator():
        try:
            while True:
                # Gelen verinin raw byte olduğundan emin olmalıyız
                data = await websocket.receive_bytes()
                yield data
        except WebSocketDisconnect:
            log.info("WebSocket disconnected")

    try:
        async for result in audio_processor.transcribe_stream(audio_chunk_generator()):
            await websocket.send_json(result)
    except Exception as e:
        log.error("Error in WebSocket transcription stream", error=str(e), exc_info=True)
        await websocket.send_json({"type": "error", "message": "An internal error occurred."})
    finally:
        if websocket.client_state != "DISCONNECTED":
            await websocket.close()
            log.info("WebSocket connection closed")