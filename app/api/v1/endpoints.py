import asyncio
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
    audio_file: UploadFile = File(...),
    logprob_threshold: Optional[float] = Form(None),
    no_speech_threshold: Optional[float] = Form(None)
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
        
        result_text = adapter.transcribe(
            resampled_audio_bytes, 
            language,
            logprob_threshold=logprob_threshold,
            no_speech_threshold=no_speech_threshold
        )
        
        log.info("Transcription successful", text_length=len(result_text))
        return {"text": result_text}

    except RuntimeError as e:
        log.error("Transcription failed because model is not ready.", error=str(e))
        raise HTTPException(status_code=503, detail="Model is not ready, please try again later.")
    except Exception as e:
        log.error("Error during transcription", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An error occurred while processing the audio file.")

@router.websocket("/transcribe-stream")
async def websocket_transcription(
    websocket: WebSocket, 
    language: Optional[str] = None,
    logprob_threshold: Optional[float] = None,
    no_speech_threshold: Optional[float] = None
):
    await websocket.accept()
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    log.info("WebSocket connection established", client=client_info, language=language)
    
    task = None
    try:
        adapter = get_adapter(websocket)
        if not adapter:
            log.warn("WebSocket connection rejected because model is not ready.", client=client_info)
            try:
                await websocket.send_json({"type": "error", "message": "Model is not ready, please try again in a moment."})
            except RuntimeError:
                pass 
            return
        
        # --- İŞTE DÜZELTME BURADA ---
        audio_processor = AudioProcessor(
            adapter=adapter, 
            language=language,
            logprob_threshold=logprob_threshold,
            no_speech_threshold=no_speech_threshold
        )

        async def audio_chunk_generator():
            try:
                while True:
                    data = await websocket.receive_bytes()
                    yield data
            except WebSocketDisconnect:
                log.info("WebSocket client disconnected.", client=client_info)
        
        async def transcribe_loop():
            async for result in audio_processor.transcribe_stream(audio_chunk_generator()):
                try:
                    await websocket.send_json(result)
                except RuntimeError:
                    log.warn("Could not send to a closed WebSocket. Breaking loop.", client=client_info)
                    break

        task = asyncio.create_task(transcribe_loop())
        await task

    except asyncio.CancelledError:
        log.info("Transcription task cancelled for client.", client=client_info)
    except Exception as e:
        log.error("Error in WebSocket main handler", client=client_info, error=str(e), exc_info=True)
    finally:
        if task and not task.done():
            task.cancel()
        
        if websocket.client_state.name == "CONNECTED":
            try:
                await websocket.close()
            except RuntimeError:
                pass
        log.info("WebSocket connection resources cleaned up.", client=client_info)