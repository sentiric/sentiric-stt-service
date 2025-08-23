// ... (mevcut dosya yükleme kodu) ...

// YENİ: Gerçek Zamanlı Transkripsiyon Mantığı
const recordBtn = document.getElementById('record-btn');
const statusText = document.getElementById('status-text');
const streamResultContainer = document.getElementById('stream-result-container');
const streamResultText = document.getElementById('stream-result-text');
const finalResultText = document.getElementById('final-result-text');

let websocket;
let mediaRecorder;
let isRecording = false;

recordBtn.addEventListener('click', () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
});

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true, video: false })
        .then(stream => {
            isRecording = true;
            recordBtn.textContent = 'Kaydı Durdur';
            statusText.textContent = 'Durum: Kaydediliyor...';
            streamResultContainer.classList.remove('hidden');
            streamResultText.textContent = '';
            finalResultText.textContent = '';
            
            const wsUrl = `ws://${window.location.host}/api/v1/transcribe-stream`;
            websocket = new WebSocket(wsUrl);

            websocket.onopen = () => {
                statusText.textContent = 'Durum: Bağlantı kuruldu, konuşun...';
                mediaRecorder = new MediaRecorder(stream);
                mediaRecorder.ondataavailable = event => {
                    if (event.data.size > 0 && websocket.readyState === WebSocket.OPEN) {
                        websocket.send(event.data);
                    }
                };
                mediaRecorder.start(250); // Her 250ms'de bir veri gönder
            };

            websocket.onmessage = event => {
                const result = JSON.parse(event.data);
                if (result.type === 'partial') {
                    streamResultText.textContent = result.text;
                } else if (result.type === 'final') {
                    finalResultText.textContent += result.text + ' ';
                    streamResultText.textContent = ''; // Geçici metni temizle
                } else if (result.type === 'error') {
                    statusText.textContent = `Hata: ${result.message}`;
                }
            };

            websocket.onclose = () => {
                statusText.textContent = 'Durum: Bağlantı kapandı.';
                stopRecording(stream);
            };
            
            websocket.onerror = (error) => {
                console.error('WebSocket Error:', error);
                statusText.textContent = 'Hata: WebSocket bağlantı hatası.';
            };

        })
        .catch(err => {
            console.error('Mikrofon erişim hatası:', err);
            statusText.textContent = 'Hata: Mikrofon erişimi reddedildi.';
        });
}

function stopRecording(stream) {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.close();
    }
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
    }
    isRecording = false;
    recordBtn.textContent = 'Kaydı Başlat';
    statusText.textContent = 'Durum: Beklemede';
}

// Sekme yönetimi
function openTab(evt, tabName) {
    // ... (sekme değiştirme JS kodu) ...
}