/**
 * Dashboard Controller
 * Main logic for the counting dashboard
 */

// ============================================
// State Management
// ============================================

const DashboardState = {
    isSessionActive: false,
    sessionStartTime: null,
    currentCount: 0,
    targetCount: 0,
    sessionId: null,
    sessionName: null,
    durationTimer: null
};

// ============================================
// Initialization
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    startStatusPolling();
    
    // Hide video overlay after image loads
    const videoFeed = document.getElementById('videoFeed');
    if (videoFeed) {
        videoFeed.addEventListener('load', () => {
            hideVideoOverlay();
        });
        
        videoFeed.addEventListener('error', () => {
            showVideoOverlay('Camera connection failed');
        });
    }
});

function initializeDashboard() {
    // Load saved RTSP URL if exists
    const savedRTSP = loadFromStorage('rtsp_url');
    if (savedRTSP) {
        setInputValue('rtspUrl', savedRTSP);
    }
    
    // Check initial session status
    updateSessionStatus();
    
    // Fetch camera stats
    updateCameraInfo();
}

// ============================================
// Event Listeners
// ============================================

function setupEventListeners() {
    // Session form
    const sessionForm = document.getElementById('sessionForm');
    if (sessionForm) {
        sessionForm.addEventListener('submit', handleStartSession);
    }
    
    // Finish button
    const finishBtn = document.getElementById('finishBtn');
    if (finishBtn) {
        finishBtn.addEventListener('click', handleFinishSession);
    }
    
    // Camera settings button
    const cameraSettingsBtn = document.getElementById('cameraSettingsBtn');
    if (cameraSettingsBtn) {
        cameraSettingsBtn.addEventListener('click', openCameraModal);
    }
}

// ============================================
// Session Management
// ============================================

async function handleStartSession(event) {
    event.preventDefault();
    
    const sessionName = getInputValue('sessionName');
    const maxCount = parseInt(getInputValue('maxCount'));
    
    if (!sessionName || !maxCount) {
        showToast('Please fill all fields', 'warning');
        return;
    }
    
    try {
        showToast('Starting session...', 'info');
        
        const response = await API.startSession(sessionName, maxCount);
        
        if (response.status === 'success') {
            showToast('Session started successfully!', 'success');
            
            // Update state
            DashboardState.isSessionActive = true;
            DashboardState.sessionStartTime = new Date();
            DashboardState.sessionId = response.session.session_id;
            DashboardState.sessionName = sessionName;
            DashboardState.targetCount = maxCount;
            
            // Update UI
            updateUIForActiveSession();
            
            // Start duration timer
            startDurationTimer();
            
            // Clear form
            setInputValue('sessionName', '');
            setInputValue('maxCount', '');
        }
    } catch (error) {
        handleAPIError(error, 'Start Session');
    }
}

async function handleFinishSession() {
    if (!confirm('Are you sure you want to finish this session?')) {
        return;
    }
    
    try {
        showToast('Finishing session...', 'info');
        
        const response = await API.finishSession();
        
        if (response.status === 'success') {
            const summary = response.summary;
            
            // Show alert based on count
            if (summary.alert_triggered) {
                const alertType = summary.alert_type === 'under' ? 'warning' : 'danger';
                const alertMessage = summary.alert_type === 'under' 
                    ? `Count is UNDER target: ${summary.final_count} / ${summary.target_count}`
                    : `Count is OVER target: ${summary.final_count} / ${summary.target_count}`;
                
                showAlertBox(alertType, 'Count Mismatch!', alertMessage);
                showToast(alertMessage, alertType, 5000);
            } else {
                showToast('Session completed successfully!', 'success');
            }
            
            // Reset state
            DashboardState.isSessionActive = false;
            stopDurationTimer();
            
            // Update UI
            updateUIForInactiveSession();
        }
    } catch (error) {
        handleAPIError(error, 'Finish Session');
    }
}

// ============================================
// Status Polling
// ============================================

function startStatusPolling() {
    // Poll every 1 second
    setInterval(updateSessionStatus, 1000);
    setInterval(updateCameraInfo, 5000);
}

async function updateSessionStatus() {
    try {
        const status = await API.getSessionStatus();
        
        if (status.active) {
            // Update counts
            const oldCount = DashboardState.currentCount;
            const newCount = status.current_count;
            
            if (newCount !== oldCount) {
                animateNumber('currentCount', oldCount, newCount);
                DashboardState.currentCount = newCount;
                
                // Play sound on count (optional)
                // playCountSound();
            }
            
            // Update target
            setElementText('targetCount', status.max_count_target);
            DashboardState.targetCount = status.max_count_target;
            
            // Update progress
            updateProgress(newCount, status.max_count_target);
            
            // Update state
            setElementText('countingState', status.state);
            
            // Update session info if not already set
            if (!DashboardState.isSessionActive) {
                DashboardState.isSessionActive = true;
                DashboardState.sessionId = status.session_id;
                DashboardState.sessionName = status.session_name;
                DashboardState.sessionStartTime = new Date(status.start_time);
                updateUIForActiveSession();
                startDurationTimer();
            }
        } else {
            if (DashboardState.isSessionActive) {
                // Session ended
                DashboardState.isSessionActive = false;
                stopDurationTimer();
                updateUIForInactiveSession();
            }
        }
    } catch (error) {
        // Silently fail status updates
        console.error('Status update failed:', error);
    }
}

async function updateCameraInfo() {
    try {
        const health = await API.getSystemHealth();
        
        if (health.camera) {
            setElementText('cameraFps', health.camera.fps);
            setElementText('cameraResolution', health.camera.resolution);
            setElementText('cameraSource', health.camera.source_type || 'Unknown');
        }
        
        if (health.ai) {
            setElementText('inferenceTime', `${health.ai.avg_inference_time_ms}ms`);
        }
    } catch (error) {
        console.error('Camera info update failed:', error);
    }
}

// ============================================
// UI Updates
// ============================================

function updateUIForActiveSession() {
    // Show/hide buttons
    toggleElement('startBtn', false);
    toggleElement('finishBtn', true);
    
    // Disable form inputs
    document.getElementById('sessionName').disabled = true;
    document.getElementById('maxCount').disabled = true;
    
    // Update status badge
    setElementHTML('sessionStatusBadge', '<span class="status-badge status-active">Active</span>');
}

function updateUIForInactiveSession() {
    // Show/hide buttons
    toggleElement('startBtn', true);
    toggleElement('finishBtn', false);
    
    // Enable form inputs
    document.getElementById('sessionName').disabled = false;
    document.getElementById('maxCount').disabled = false;
    
    // Update status badge
    setElementHTML('sessionStatusBadge', '<span class="status-badge status-inactive">Inactive</span>');
    
    // Reset counts
    setElementText('currentCount', '0');
    setElementText('targetCount', '0');
    setElementText('countingState', 'IDLE');
    updateProgress(0, 1);
    
    // Hide alert
    toggleElement('alertBox', false);
}

function updateProgress(current, target) {
    const percent = formatPercentage(current, target);
    document.getElementById('progressFill').style.width = `${percent}%`;
    setElementText('progressPercent', `${percent}%`);
}

function showAlertBox(type, title, message) {
    const alertBox = document.getElementById('alertBox');
    alertBox.className = `alert alert-${type}`;
    setElementText('alertTitle', title);
    setElementText('alertMessage', message);
    toggleElement('alertBox', true);
}

// ============================================
// Duration Timer
// ============================================

function startDurationTimer() {
    stopDurationTimer();  // Clear any existing timer
    
    DashboardState.durationTimer = setInterval(() => {
        if (DashboardState.sessionStartTime) {
            const now = new Date();
            const elapsed = Math.floor((now - DashboardState.sessionStartTime) / 1000);
            setElementText('sessionDuration', formatDuration(elapsed));
        }
    }, 1000);
}

function stopDurationTimer() {
    if (DashboardState.durationTimer) {
        clearInterval(DashboardState.durationTimer);
        DashboardState.durationTimer = null;
    }
}

// ============================================
// Camera Modal
// ============================================

function openCameraModal() {
    document.getElementById('cameraModal').style.display = 'flex';
}

function closeCameraModal() {
    document.getElementById('cameraModal').style.display = 'none';
}

async function updateRTSP() {
    const rtspUrl = getInputValue('rtspUrl');
    
    if (!rtspUrl) {
        showToast('Please enter RTSP URL', 'warning');
        return;
    }
    
    try {
        showToast('Updating RTSP URL...', 'info');
        
        const response = await API.setRTSP(rtspUrl);
        
        if (response.status === 'success') {
            showToast('RTSP URL updated!', 'success');
            saveToStorage('rtsp_url', rtspUrl);
            closeCameraModal();
            
            // Reload video feed
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
    } catch (error) {
        handleAPIError(error, 'Update RTSP');
    }
}

async function uploadVideo() {
    const fileInput = document.getElementById('videoFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showToast('Please select a video file', 'warning');
        return;
    }
    
    try {
        showToast('Uploading video...', 'info');
        
        const formData = new FormData();
        formData.append('video', file);
        
        const response = await API.uploadVideo(formData);
        
        if (response.status === 'success') {
            showToast('Video uploaded successfully!', 'success');
            closeCameraModal();
            
            // Reload video feed
            setTimeout(() => {
                location.reload();
            }, 1000);
        }
    } catch (error) {
        handleAPIError(error, 'Upload Video');
    }
}

// ============================================
// Optional: Sound Notification
// ============================================

function playCountSound() {
    // Create audio context
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.value = 800;  // Frequency in Hz
    oscillator.type = 'sine';
    
    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.2);
}
