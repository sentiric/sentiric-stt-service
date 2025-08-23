import structlog
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Optional
from app.services.stt_service import transcribe_audio
from app.utils.audio import resample_audio
from app.services.streaming_service import AudioProcessor

router = APIRouter()
log = structlog.get_logger(__name__)

class TranscriptionResponse(BaseModel):
    text: str

@router.post("/transcribe", response_model=TranscriptionResponse, tags=["Speech-to-Text (Dosya)"])
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
        resampled_audio_bytes = resample_audio(audio_bytes)
        
        log.info("Transcription request received", filename=audio_file.filename, language=language or "auto", size_kb=round(len(audio_bytes) / 1024, 2))
        
        result_text = transcribe_audio(resampled_audio_bytes, language)
        
        log.info(
            "Transcription successful",
            text_length=len(result_text),
            text_snippet_start=result_text[:20],
            text_snippet_end=result_text[-20:],
            text_hash=hash(result_text)
        )
        return {"text": result_text}

    except Exception as e:
        log.error("Error during transcription", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing the audio file.")

@router.websocket("/transcribe-stream")
async def websocket_transcription(websocket: WebSocket, language: Optional[str] = None):
    await websocket.accept()
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    log.info("WebSocket connection established", client=client_info, language=language)
    
    try:
        audio_processor = AudioProcessor(language=language)

        async def audio_chunk_generator():
            try:
                while True:
                    data = await websocket.receive_bytes()
                    yield data
            except WebSocketDisconnect:
                log.info("WebSocket client disconnected.", client=client_info)

        async for result in audio_processor.transcribe_stream(audio_chunk_generator()):
            await websocket.send_json(result)

    except Exception as e:
        log.error("Error in WebSocket transcription stream", client=client_info, error=str(e), exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": "An internal error occurred."})
        except RuntimeError:
            pass # Bağlantı zaten kapalı olabilir
    finally:
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()
        log.info("WebSocket connection closed", client=client_info)