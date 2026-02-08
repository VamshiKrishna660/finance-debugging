// ========================================
// Configuration
// ========================================
const API_BASE_URL = 'http://localhost:8000';
const POLL_INTERVAL = 2000; // 2 seconds
const MAX_POLL_TIME = 600000; // 10 minutes

// ========================================
// State Management
// ========================================
const state = {
    selectedFile: null,
    currentJobId: null,
    pollingInterval: null,
    startTime: null,
    elapsedInterval: null
};

// ========================================
// DOM Elements
// ========================================
const elements = {
    uploadZone: document.getElementById('uploadZone'),
    fileInput: document.getElementById('fileInput'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    btnRemove: document.getElementById('btnRemove'),
    queryInput: document.getElementById('queryInput'),
    btnAnalyze: document.getElementById('btnAnalyze'),

    apiStatus: document.getElementById('apiStatus'),

    queuedJobs: document.getElementById('queuedJobs'),
    activeWorkers: document.getElementById('activeWorkers'),
    currentRuntime: document.getElementById('currentRuntime'),

    jobStatusSection: document.getElementById('jobStatusSection'),
    jobId: document.getElementById('jobId'),
    jobStatus: document.getElementById('jobStatus'),
    elapsedTime: document.getElementById('elapsedTime'),
    progressFill: document.getElementById('progressFill'),
    jobTimestamps: document.getElementById('jobTimestamps'),
    createdAt: document.getElementById('createdAt'),
    startedAt: document.getElementById('startedAt'),
    endedAt: document.getElementById('endedAt'),

    resultsSection: document.getElementById('resultsSection'),
    resultsContent: document.getElementById('resultsContent'),
    jobMetadata: document.getElementById('jobMetadata'),
    btnDownload: document.getElementById('btnDownload')
};

// ========================================
// Utility Functions
// ========================================
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

function formatElapsedTime(ms) {
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (hours > 0) {
        return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
    } else if (minutes > 0) {
        return `${minutes}m ${seconds % 60}s`;
    } else {
        return `${seconds}s`;
    }
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '--';
    try {
        const date = new Date(timestamp);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: true
        });
    } catch (e) {
        return '--';
    }
}

function calculateRuntime(startTime, endTime) {
    if (!startTime) return '--';
    const start = new Date(startTime).getTime();
    const end = endTime ? new Date(endTime).getTime() : Date.now();
    return formatElapsedTime(end - start);
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'error' ? 'rgba(239, 68, 68, 0.95)' :
            type === 'success' ? 'rgba(16, 185, 129, 0.95)' :
                'rgba(59, 130, 246, 0.95)'};
        color: white;
        border-radius: 12px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        z-index: 1000;
        animation: slideIn 0.3s ease;
        backdrop-filter: blur(10px);
        max-width: 400px;
        font-weight: 500;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Add animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// ========================================
// API Functions
// ========================================
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/`);
        const data = await response.json();

        updateAPIStatus(true, data.queue_enabled);
        startQueueStatsPolling();
        return true;
    } catch (error) {
        updateAPIStatus(false);
        console.error('API connection failed:', error);
        return false;
    }
}

function updateAPIStatus(online, queueEnabled = false) {
    const statusDot = elements.apiStatus.querySelector('.status-dot');
    const statusText = elements.apiStatus.querySelector('.status-text');

    if (online) {
        statusDot.classList.add('online');
        statusDot.classList.remove('offline');
        statusText.textContent = queueEnabled ? 'API Online (Queue Active)' : 'API Online';
    } else {
        statusDot.classList.add('offline');
        statusDot.classList.remove('online');
        statusText.textContent = 'API Offline';
    }
}

async function uploadDocument() {
    if (!state.selectedFile) {
        showNotification('Please select a file first', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', state.selectedFile);

    const query = elements.queryInput.value.trim() ||
        'Analyze this financial document for investment insights';
    formData.append('query', query);

    try {
        elements.btnAnalyze.disabled = true;
        elements.btnAnalyze.classList.add('loading');
        elements.btnAnalyze.textContent = 'Uploading...';

        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        const data = await response.json();

        state.currentJobId = data.job_id;
        state.startTime = Date.now();

        showNotification('Document uploaded successfully! Analysis started.', 'success');

        // Show job status section
        elements.jobStatusSection.style.display = 'block';
        elements.jobId.textContent = data.job_id;

        // Hide OUTPUT section until job completes
        elements.resultsSection.style.display = 'none';
        elements.resultsContent.innerHTML = '';
        elements.jobMetadata.innerHTML = '';

        // Start polling
        startJobPolling();
        startElapsedTimer();

    } catch (error) {
        console.error('Upload error:', error);
        showNotification(`Upload failed: ${error.message}`, 'error');
    } finally {
        elements.btnAnalyze.disabled = false;
        elements.btnAnalyze.classList.remove('loading');
        elements.btnAnalyze.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M10 3V17M3 10H17" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            Analyze Document
        `;
    }
}

async function pollJobStatus() {
    if (!state.currentJobId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/job/${state.currentJobId}/status`);
        const data = await response.json();

        updateJobStatus(data);

        // Update current runtime in queue stats if job is running
        if (data.status === 'started' && data.started_at) {
            const runtime = calculateRuntime(data.started_at);
            elements.currentRuntime.textContent = runtime;
        } else if (data.status === 'finished' && data.started_at && data.ended_at) {
            const totalTime = calculateRuntime(data.started_at, data.ended_at);
            elements.currentRuntime.textContent = totalTime;
        }

        if (data.status === 'finished') {
            stopJobPolling();
            stopElapsedTimer();
            await fetchJobResult();
        } else if (data.status === 'failed') {
            stopJobPolling();
            stopElapsedTimer();
            showNotification('Job failed: ' + (data.error || 'Unknown error'), 'error');
        }

    } catch (error) {
        console.error('Status polling error:', error);
    }
}

async function fetchJobResult() {
    if (!state.currentJobId) return;

    try {
        const response = await fetch(`${API_BASE_URL}/job/${state.currentJobId}/result`);
        const data = await response.json();

        if (data.status === 'success') {
            displayResults(data);
            showNotification('Analysis completed successfully!', 'success');
        } else {
            showNotification('Failed to retrieve results', 'error');
        }

    } catch (error) {
        console.error('Result fetch error:', error);
        showNotification('Error retrieving results', 'error');
    }
}

async function fetchQueueStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/queue/stats`);
        const data = await response.json();

        elements.queuedJobs.textContent = data.pending || 0;
        elements.activeWorkers.textContent = data.workers || 0;

    } catch (error) {
        console.error('Queue stats error:', error);
    }
}

// ========================================
// UI Update Functions
// ========================================
function updateJobStatus(data) {
    const status = data.status || 'unknown';

    elements.jobStatus.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    elements.jobStatus.className = `job-status-badge ${status}`;

    // Update timestamps if available
    if (data.created_at || data.started_at || data.ended_at) {
        elements.jobTimestamps.style.display = 'grid';
        if (data.created_at) {
            elements.createdAt.textContent = formatTimestamp(data.created_at);
        }
        if (data.started_at) {
            elements.startedAt.textContent = formatTimestamp(data.started_at);
        }
        if (data.ended_at) {
            elements.endedAt.textContent = formatTimestamp(data.ended_at);
        }
    }

    // Update progress bar
    let progress = 0;
    switch (status) {
        case 'queued':
            progress = 25;
            break;
        case 'started':
            progress = 50;
            break;
        case 'finished':
            progress = 100;
            break;
        case 'failed':
            progress = 100;
            elements.progressFill.style.background = 'var(--error)';
            break;
    }

    elements.progressFill.style.width = `${progress}%`;
}

function displayResults(data) {
    // Only show OUTPUT section when we have actual results
    if (!data || !data.analysis) {
        return;
    }

    // Show the OUTPUT section
    elements.resultsSection.style.display = 'block';

    const analysis = data.analysis;
    const query = data.query || elements.queryInput.value || 'Default analysis';
    const message = data.message || 'Analysis completed';

    // Calculate runtime metrics if timestamps are available
    let runtimeMetrics = '';
    if (data.created_at || data.started_at || data.ended_at) {
        const createdTime = data.created_at ? new Date(data.created_at).getTime() : null;
        const startedTime = data.started_at ? new Date(data.started_at).getTime() : null;
        const endedTime = data.ended_at ? new Date(data.ended_at).getTime() : null;

        if (createdTime && startedTime && endedTime) {
            const waitingTime = formatElapsedTime(startedTime - createdTime);
            const processingTime = formatElapsedTime(endedTime - startedTime);
            const totalTime = formatElapsedTime(endedTime - createdTime);

            runtimeMetrics = `
RUNTIME METRICS:
  • Waiting Time:    ${waitingTime}
  • Processing Time: ${processingTime}
  • Total Time:      ${totalTime}
`;
        }
    }

    // Format the metadata section
    const metadataHTML = `
        <div class="metadata-grid">
            <div class="metadata-item">
                <span class="metadata-label">Job ID:</span>
                <code class="metadata-value">${state.currentJobId}</code>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Query:</span>
                <span class="metadata-value">${query}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Status:</span>
                <span class="metadata-value metadata-status-success">${message}</span>
            </div>
            <div class="metadata-item">
                <span class="metadata-label">Completed:</span>
                <span class="metadata-value">${formatTimestamp(data.ended_at || new Date())}</span>
            </div>
        </div>
    `;

    elements.jobMetadata.innerHTML = metadataHTML;

    // Display the OUTPUT - Clean format showing only the final crew analysis
    const outputDisplay = `
═══════════════════════════════════════════════════════════════
  OUTPUT
═══════════════════════════════════════════════════════════════

Job ID: ${state.currentJobId}
Query:  ${query}
${runtimeMetrics}
═══════════════════════════════════════════════════════════════

${analysis}

═══════════════════════════════════════════════════════════════
  END OF OUTPUT
═══════════════════════════════════════════════════════════════
    `.trim();

    elements.resultsContent.innerHTML = `<pre>${outputDisplay}</pre>`;

    // Store for download
    elements.btnDownload.dataset.results = outputDisplay;
}

// ========================================
// Timer Functions
// ========================================
function startElapsedTimer() {
    state.elapsedInterval = setInterval(() => {
        const elapsed = Date.now() - state.startTime;
        elements.elapsedTime.textContent = formatElapsedTime(elapsed);
    }, 1000);
}

function stopElapsedTimer() {
    if (state.elapsedInterval) {
        clearInterval(state.elapsedInterval);
        state.elapsedInterval = null;
    }
}

function startJobPolling() {
    state.pollingInterval = setInterval(pollJobStatus, POLL_INTERVAL);

    // Stop polling after max time
    setTimeout(() => {
        if (state.pollingInterval) {
            stopJobPolling();
            showNotification('Polling timeout - job may still be processing', 'warning');
        }
    }, MAX_POLL_TIME);
}

function stopJobPolling() {
    if (state.pollingInterval) {
        clearInterval(state.pollingInterval);
        state.pollingInterval = null;
    }
}

function startQueueStatsPolling() {
    fetchQueueStats();
    setInterval(fetchQueueStats, 5000); // Update every 5 seconds
}

// ========================================
// File Upload Handlers
// ========================================
function handleFileSelect(file) {
    if (!file) return;

    // Validate file type
    if (file.type !== 'application/pdf') {
        showNotification('Please select a PDF file', 'error');
        return;
    }

    state.selectedFile = file;

    // Update UI
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.fileInfo.style.display = 'flex';
    elements.uploadZone.style.display = 'none';
    elements.btnAnalyze.disabled = false;
}

function removeFile() {
    state.selectedFile = null;
    elements.fileInfo.style.display = 'none';
    elements.uploadZone.style.display = 'flex';
    elements.btnAnalyze.disabled = true;
    elements.fileInput.value = '';
}

function downloadResults() {
    const results = elements.btnDownload.dataset.results;
    if (!results) return;

    const blob = new Blob([results], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analysis_${state.currentJobId}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showNotification('Results downloaded', 'success');
}

// ========================================
// Event Listeners
// ========================================
document.addEventListener('DOMContentLoaded', () => {
    // Check API status on load
    checkAPIStatus();

    // Upload zone click
    elements.uploadZone.addEventListener('click', () => {
        elements.fileInput.click();
    });

    // File input change
    elements.fileInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        handleFileSelect(file);
    });

    // Drag and drop
    elements.uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.add('drag-over');
    });

    elements.uploadZone.addEventListener('dragleave', () => {
        elements.uploadZone.classList.remove('drag-over');
    });

    elements.uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        elements.uploadZone.classList.remove('drag-over');

        const file = e.dataTransfer.files[0];
        handleFileSelect(file);
    });

    // Remove file button
    elements.btnRemove.addEventListener('click', (e) => {
        e.stopPropagation();
        removeFile();
    });

    // Analyze button
    elements.btnAnalyze.addEventListener('click', uploadDocument);

    // Download button
    elements.btnDownload.addEventListener('click', downloadResults);

    // Enter key in query input
    elements.queryInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && e.ctrlKey && !elements.btnAnalyze.disabled) {
            uploadDocument();
        }
    });
});

// ========================================
// Console Info
// ========================================
console.log('%c Financial Document Analyzer ', 'background: linear-gradient(135deg, #8B5CF6, #EC4899); color: white; font-size: 16px; padding: 8px 16px; border-radius: 8px; font-weight: bold;');
console.log('%c Frontend v1.0.0 | Connected to API: ' + API_BASE_URL, 'color: #A78BFA; font-size: 12px;');
