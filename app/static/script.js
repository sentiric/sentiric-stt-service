document.getElementById('transcribe-form').addEventListener('submit', async function(event) {
    event.preventDefault();

    const form = event.target;
    const formData = new FormData(form);
    
    const resultContainer = document.getElementById('result-container');
    const resultText = document.getElementById('result-text');
    const errorMessage = document.getElementById('error-message');
    const spinner = document.getElementById('spinner');
    const submitBtn = document.getElementById('submit-btn');

    // Reset UI
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
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        resultText.textContent = data.text;
        
    } catch (error) {
        console.error('Transcription error:', error);
        errorMessage.textContent = `Hata: ${error.message}`;
        errorMessage.classList.remove('hidden');
    } finally {
        spinner.classList.add('hidden');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Metne Çevir';
    }
});