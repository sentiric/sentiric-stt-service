import asyncio # YENİ
import structlog
from fastapi import APIRouter, UploadFile, File, HTTPException, Form, WebSocket, WebSocketDisconnect, Request
from pydantic import BaseModel
from typing import Optional
from app.utils.audio import resample_audio
from app.services.stt_service import get_adapter
from app.services.streaming_service import AudioProcessor

router = APIRouter()
log = structlog.get_logger(__name__)

class TranscriptionResponse(BaseModel):
    text: str
@router.post("/transcribe", response_model=TranscriptionResponse, tags=["Speech-to-Text (Dosya)"])
async def create_transcription(
    request: Request,
    language: Optional[str] = Form(None), 
    audio_file: UploadFile = File(...)
):
    if not (audio_file.content_type and audio_file.content_type.startswith("audio/")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")
    
    try:
        adapter = get_adapter(request)
        if not adapter:
            raise RuntimeError("STT Adapter not ready")
            
        audio_bytes = await audio_file.read()
        resampled_audio_bytes = resample_audio(audio_bytes)
        log.info("Transcription request received", filename=audio_file.filename, language=language or "auto", size_kb=round(len(audio_bytes) / 1024, 2))
        
        result_text = adapter.transcribe(resampled_audio_bytes, language)
        
        log.info("Transcription successful", text_length=len(result_text))
        return {"text": result_text}

    except RuntimeError as e:
        log.error("Transcription failed because model is not ready.", error=str(e))
        raise HTTPException(status_code=503, detail="Model is not ready, please try again later.")
    except Exception as e:
        log.error("Error during transcription", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing the audio file.")


@router.websocket("/transcribe-stream")
async def websocket_transcription(websocket: WebSocket, language: Optional[str] = None):
    await websocket.accept()
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    log.info("WebSocket connection established", client=client_info, language=language)
    
    task = None
    try:
        adapter = get_adapter(websocket)
        if not adapter:
            await websocket.send_json({"type": "error", "message": "Model is not ready, please try again in a moment."})
            await websocket.close(code=1011) # 1011 = Internal Error
            log.warn("WebSocket connection rejected because model is not ready.", client=client_info)
            return
        
        audio_processor = AudioProcessor(adapter=adapter, language=language)

        async def audio_chunk_generator():
            try:
                while True:
                    data = await websocket.receive_bytes()
                    yield data
            except WebSocketDisconnect:
                log.info("WebSocket client disconnected.", client=client_info)

        # Ana transkripsiyon döngüsünü bir asyncio Task olarak başlat
        async def transcribe_loop():
            async for result in audio_processor.transcribe_stream(audio_chunk_generator()):
                await websocket.send_json(result)
        
        task = asyncio.create_task(transcribe_loop())
        await task

    except asyncio.CancelledError:
        log.info("Transcription task cancelled for client.", client=client_info)
    except Exception as e:
        log.error("Error in WebSocket main handler", client=client_info, error=str(e), exc_info=True)
    finally:
        # Bağlantı kapandığında, eğer görev hala çalışıyorsa zorla iptal et.
        if task and not task.done():
            task.cancel()
        
        if websocket.client_state.name != "DISCONNECTED":
            await websocket.close()
        log.info("WebSocket connection resources cleaned up.", client=client_info)