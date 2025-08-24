document.addEventListener('DOMContentLoaded', () => {
    // Sekme yönetimi
    const tabs = document.querySelectorAll('.tab-link');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(item => item.classList.remove('active'));
            tab.classList.add('active');

            const target = document.querySelector(`#${tab.dataset.tab}`);
            tabContents.forEach(content => content.classList.remove('active'));
            target.classList.add('active');
        });
    });

    // Dosya Yükleme Mantığı
    const transcribeForm = document.getElementById('transcribe-form');
    transcribeForm.addEventListener('submit', async function(event) {
        event.preventDefault();

        const form = event.target;
        const formData = new FormData(form);
        
        const logprobThreshold = document.getElementById('logprob-threshold').value;
        const noSpeechThreshold = document.getElementById('no-speech-threshold').value;
        formData.append('logprob_threshold', logprobThreshold);
        formData.append('no_speech_threshold', noSpeechThreshold);

        const resultContainer = document.getElementById('file-result-container');
        const resultText = document.getElementById('file-result-text');
        const errorMessage = document.getElementById('file-error-message');
        const spinner = document.getElementById('file-spinner');
        const submitBtn = document.getElementById('submit-btn');

        resultContainer.classList.remove('hidden');
        resultText.textContent = '';
        errorMessage.classList.add('hidden');
        spinner.classList.remove('hidden');
        submitBtn.disabled = true;
        submitBtn.textContent = 'İşleniyor...';

        try {
            const response = await fetch('/api/v1/transcribe', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || `HTTP hatası! Durum: ${response.status}`);
            }

            const data = await response.json();
            resultText.textContent = data.text;
            
        } catch (error) {
            console.error('Transkripsiyon hatası:', error);
            errorMessage.textContent = `Hata: ${error.message}`;
            errorMessage.classList.remove('hidden');
        } finally {
            spinner.classList.add('hidden');
            submitBtn.disabled = false;
            submitBtn.textContent = 'Metne Çevir';
        }
    });

    // Gerçek Zamanlı Transkripsiyon Mantığı
    const recordBtn = document.getElementById('record-btn');
    const statusText = document.getElementById('status-text');
    const streamResultContainer = document.getElementById('stream-result-container');
    const finalResultText = document.getElementById('final-result-text');
    const streamErrorMessage = document.getElementById('stream-error-message');
    const languageStreamInput = document.getElementById('language-stream');

    let websocket;
    let audioContext;
    let processor;
    let isRecording = false;
    let mediaStream;

    recordBtn.addEventListener('click', () => {
        if (isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    });

    async function startRecording() {
        try {
            mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
            
            isRecording = true;
            recordBtn.textContent = '🛑 Kaydı Durdur';
            recordBtn.classList.add('recording');
            statusText.textContent = 'Durum: Bağlanılıyor...';
            streamResultContainer.classList.remove('hidden');
            streamErrorMessage.classList.add('hidden');
            finalResultText.textContent = '';
            
            const logprobThreshold = document.getElementById('logprob-threshold').value;
            const noSpeechThreshold = document.getElementById('no-speech-threshold').value;
            const language = languageStreamInput.value.trim();
            
            const params = new URLSearchParams();
            if (language) params.append('language', language);
            if (logprobThreshold) params.append('logprob_threshold', logprobThreshold);
            if (noSpeechThreshold) params.append('no_speech_threshold', noSpeechThreshold);

            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/api/v1/transcribe-stream?${params.toString()}`;
            websocket = new WebSocket(wsUrl);

            websocket.onopen = () => {
                statusText.textContent = 'Durum: Bağlantı kuruldu, konuşabilirsiniz...';
                audioContext = new AudioContext({ sampleRate: 16000 });
                const source = audioContext.createMediaStreamSource(mediaStream);
                processor = audioContext.createScriptProcessor(1024, 1, 1);

                source.connect(processor);
                processor.connect(audioContext.destination);

                processor.onaudioprocess = (e) => {
                    if (!isRecording) return;
                    const inputData = e.inputBuffer.getChannelData(0);
                    const int16Data = new Int16Array(inputData.length);
                    for (let i = 0; i < inputData.length; i++) {
                        int16Data[i] = Math.max(-1, Math.min(1, inputData[i])) * 32767;
                    }
                    if (websocket.readyState === WebSocket.OPEN) {
                        websocket.send(int16Data.buffer);
                    }
                };
            };

            websocket.onmessage = event => {
                const result = JSON.parse(event.data);
                if (result.type === 'final' && result.text) {
                    finalResultText.textContent += result.text + ' ';
                } else if (result.type === 'error') {
                    streamErrorMessage.textContent = `Hata: ${result.message}`;
                    streamErrorMessage.classList.remove('hidden');
                }
            };

            websocket.onclose = () => {
                statusText.textContent = 'Durum: Bağlantı kapandı.';
                if(isRecording) stopRecording();
            };
            
            websocket.onerror = (error) => {
                console.error('WebSocket Hatası:', error);
                streamErrorMessage.textContent = 'Hata: WebSocket bağlantı hatası.';
                streamErrorMessage.classList.remove('hidden');
                if(isRecording) stopRecording();
            };

        } catch (err) {
            console.error('Mikrofon erişim hatası:', err);
            statusText.textContent = 'Hata: Mikrofon erişimi reddedildi veya bulunamadı.';
        }
    }

    function stopRecording() {
        if (!isRecording) return;
        isRecording = false;

        if (processor) {
            processor.disconnect();
            processor = null;
        }
        if (audioContext) {
            audioContext.close();
            audioContext = null;
        }
        if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.close();
        }
        if(mediaStream) {
             mediaStream.getTracks().forEach(track => track.stop());
             mediaStream = null;
        }
        
        recordBtn.textContent = '🎤 Kaydı Başlat';
        recordBtn.classList.remove('recording');
        statusText.textContent = 'Durum: Beklemede';
    }
});