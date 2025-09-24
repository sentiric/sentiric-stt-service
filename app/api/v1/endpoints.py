# sentiric-stt-service/app/api/v1/endpoints.py
import asyncio
import structlog
from fastapi import (
    APIRouter, UploadFile, File, HTTPException, Form, 
    WebSocket, WebSocketDisconnect, Request, status
)
from pydantic import BaseModel
from typing import Optional
from app.utils.audio import resample_audio
from app.services.stt_service import get_adapter
from app.services.streaming_service import AudioProcessor
from uvicorn.protocols.utils import ClientDisconnected

router = APIRouter()
log = structlog.get_logger(__name__)

class TranscriptionResponse(BaseModel):
    text: str

@router.post(
    "/transcribe", 
    response_model=TranscriptionResponse, 
    tags=["Speech-to-Text (Dosya)"],
    summary="Bir ses dosyasını metne çevirir."
)
async def create_transcription(
    request: Request,
    language: Optional[str] = Form(None), 
    audio_file: UploadFile = File(...),
    logprob_threshold: Optional[float] = Form(None),
    no_speech_threshold: Optional[float] = Form(None)
):
    """
    Bir ses dosyasını yükleyerek metne çevirir. Farklı ses formatlarını destekler.
    """
    if not (audio_file.content_type and audio_file.content_type.startswith("audio/")):
        log.warn("Geçersiz dosya tipi yüklendi.", content_type=audio_file.content_type, filename=audio_file.filename)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid file type: {audio_file.content_type}. Please upload an audio file.")
    
    adapter = get_adapter(request)
    if not adapter:
        log.error("Transkripsiyon isteği alındı ancak model hazır değil.")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Model is not ready, please try again later.")
        
    normalized_language = language.lower() if language and language.strip() else None
    
    log.info(
        "Dosya transkripsiyon isteği alındı.", 
        filename=audio_file.filename, 
        language=normalized_language or "auto", 
        content_type=audio_file.content_type
    )
            
    try:
        audio_bytes = await audio_file.read()
        log.debug("Ses dosyası başarıyla okundu.", original_size_kb=round(len(audio_bytes) / 1024, 2))

        resampled_audio_bytes = resample_audio(audio_bytes)
        
        result_text = adapter.transcribe(
            resampled_audio_bytes, 
            normalized_language,
            logprob_threshold=logprob_threshold,
            no_speech_threshold=no_speech_threshold
        )
        
        log.info("Dosya transkripsiyonu başarıyla tamamlandı.", text_length=len(result_text))
        log.debug("Transkripsiyon sonucu", transcribed_text=result_text)
        return {"text": result_text}

    except Exception as e:
        log.error("Transkripsiyon sırasında beklenmedik bir hata oluştu.", error=str(e), exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while processing the audio file.")

@router.websocket("/transcribe-stream")
async def websocket_transcription(
    websocket: WebSocket, 
    language: Optional[str] = None,
    logprob_threshold: Optional[float] = None,
    no_speech_threshold: Optional[float] = None,
    vad_aggressiveness: Optional[int] = None
):
    """
    Gerçek zamanlı ses akışını WebSocket üzerinden metne çevirir.
    """
    await websocket.accept()
    client_info = f"{websocket.client.host}:{websocket.client.port}"
    normalized_language = language.lower() if language and language.strip() else None
    
    log.info("WebSocket bağlantısı kuruldu.", client=client_info, language=normalized_language or "auto")
    
    adapter = get_adapter(websocket)
    if not adapter:
        log.warn("WebSocket bağlantısı reddedildi çünkü model hazır değil.", client=client_info)
        await websocket.close(code=status.WS_1013_TRY_AGAIN_LATER, reason="Model is not ready, please try again in a moment.")
        return
        
    audio_processor = AudioProcessor(
        adapter=adapter, 
        language=normalized_language,
        vad_aggressiveness=vad_aggressiveness,
        logprob_threshold=logprob_threshold,
        no_speech_threshold=no_speech_threshold
    )

    async def audio_chunk_generator():
        try:
            while True:
                data = await websocket.receive_bytes()
                yield data
        except WebSocketDisconnect:
            log.info("WebSocket istemcisi bağlantıyı kapattı.", client=client_info)
    
    transcribe_task = None
    try:
        async def transcribe_loop():
            async for result in audio_processor.transcribe_stream(audio_chunk_generator()):
                try:
                    await websocket.send_json(result)
                except (WebSocketDisconnect, ClientDisconnected, RuntimeError):
                    log.warn("Kapalı bir WebSocket'e gönderim yapılamadı. İstemci muhtemelen ayrıldı.", client=client_info)
                    break 

        transcribe_task = asyncio.create_task(transcribe_loop())
        await transcribe_task

    except asyncio.CancelledError:
        log.info("Transkripsiyon görevi iptal edildi.", client=client_info)
    except Exception as e:
        log.error("WebSocket ana işleyicisinde beklenmedik hata.", client=client_info, error=str(e), exc_info=True)
    finally:
        if transcribe_task and not transcribe_task.done():
            transcribe_task.cancel()
        
        if websocket.client_state.name == "CONNECTED":
            try:
                # İstemciye normal bir kapanış mesajı gönder
                await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
            except (WebSocketDisconnect, ClientDisconnected, RuntimeError):
                pass # Zaten kapalıysa sorun değil
        log.info("WebSocket bağlantı kaynakları temizlendi.", client=client_info)