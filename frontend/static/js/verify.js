// Document verification functionality

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('fileInput').addEventListener('change', handleFileSelect);
    document.getElementById('verifyForm').addEventListener('submit', handleVerify);
});

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        document.getElementById('fileLabel').textContent = file.name;
    }
}

// Handle document verification
async function handleVerify(event) {
    event.preventDefault();

    const fileInput = document.getElementById('fileInput');
    const file = fileInput.files[0];

    if (!file) {
        alert('Please select a file!');
        return;
    }

    // Show processing
    document.getElementById('processingSection').classList.remove('hidden');
    document.getElementById('resultSection').classList.add('hidden');

    try {
        // Send file to backend for verification
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/verify', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Failed to verify document');
        }

        const data = await response.json();

        // Hide processing
        document.getElementById('processingSection').classList.add('hidden');

        // Show result
        if (data.notarized) {
            showResult('success', '✅ Document Verified!', 
                `<p>This document has been notarized on the blockchain.</p>
                 <p><strong>File:</strong> ${file.name}</p>
                 <p><strong>Document Hash:</strong></p>
                 <div class="hash-display">${data.hash}</div>
                 <p><strong>Notarized On:</strong> ${data.date}</p>
                 <p><strong>Timestamp:</strong> ${data.timestamp}</p>
                 <p class="success-message">✓ This document is authentic and has not been tampered with.</p>`);
        } else {
            showResult('info', 'ℹ️ Document Not Found', 
                `<p>This document has not been notarized on the blockchain.</p>
                 <p><strong>File:</strong> ${file.name}</p>
                 <p><strong>Document Hash:</strong></p>
                 <div class="hash-display">${data.hash}</div>
                 <p>If you believe this document should be notarized, please check:</p>
                 <ul>
                     <li>You uploaded the correct file</li>
                     <li>The file has not been modified</li>
                     <li>The notarization transaction was successful</li>
                 </ul>`);
        }

    } catch (error) {
        console.error('Error verifying document:', error);
        document.getElementById('processingSection').classList.add('hidden');
        showResult('error', 'Verification Failed', error.message);
    }
}

// Show result message
function showResult(type, title, message) {
    document.getElementById('resultSection').classList.remove('hidden');

    const resultContent = document.getElementById('resultContent');
    let className = 'info-message';
    
    if (type === 'success') {
        className = 'success-message';
    } else if (type === 'error') {
        className = 'error-message';
    }

    resultContent.innerHTML = `
        <div class="${className}">
            <h3>${title}</h3>
            ${message}
            <button onclick="location.reload()" class="btn btn-primary" style="margin-top: 1rem;">
                Verify Another Document
            </button>
        </div>
    `;
}
