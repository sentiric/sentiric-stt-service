import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import os
import soundfile as sf
import numpy as np

# ASGITransport kullanarak app'imizi bir test sunucusu gibi sarmalıyoruz.
# base_url zorunludur.
transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_health_check():
    """
    /health endpoint'inin 200 OK ve doğru formatta yanıt verdiğini test eder.
    """
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    json_response = response.json()
    assert json_response["status"] == "ok"
    assert json_response["model_loaded"] is True

@pytest.mark.asyncio
async def test_transcribe_audio_valid_file(tmp_path):
    """
    /transcribe endpoint'ine geçerli bir ses dosyası gönderildiğinde
    200 OK yanıtı ve metin döndürdüğünü test eder.
    """
    # Geçici bir WAV dosyası oluştur
    sample_wav_path = tmp_path / "sample.wav"
    samplerate = 16000
    data = np.zeros(samplerate)  # 1 saniyelik sessizlik
    sf.write(sample_wav_path, data, samplerate)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with open(sample_wav_path, "rb") as f:
            files = {"audio_file": ("sample.wav", f, "audio/wav")}
            response = await ac.post("/api/v1/transcribe", files=files)

    assert response.status_code == 200
    json_response = response.json()
    assert "text" in json_response
    assert isinstance(json_response["text"], str)

@pytest.mark.asyncio
async def test_transcribe_invalid_file_type():
    """
    /transcribe endpoint'ine ses dosyası dışında bir dosya gönderildiğinde
    400 Bad Request hatası verdiğini test eder.
    """
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"audio_file": ("test.txt", b"this is not audio", "text/plain")}
        response = await ac.post("/api/v1/transcribe", files=files)
    
    assert response.status_code == 400
    assert "Geçersiz dosya tipi" in response.json()["detail"]