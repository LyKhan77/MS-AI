/**
 * Utility Functions
 * Common helper functions for the application
 */

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = 'info', duration = 3000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <div>${message}</div>
    `;
    
    container.appendChild(toast);
    
    // Auto-remove after duration
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ============================================
// Time Formatting
// ============================================

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    return `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

// ============================================
// Number Formatting
// ============================================

function formatPercentage(value, total) {
    if (total === 0) return 0;
    return Math.round((value / total) * 100);
}

function formatConfidence(confidence) {
    return Math.round(confidence * 100);
}

// ============================================
// DOM Helpers
// ============================================

function setElementText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function setElementHTML(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
}

function toggleElement(id, show) {
    const el = document.getElementById(id);
    if (el) el.style.display = show ? 'block' : 'none';
}

function setInputValue(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value;
}

function getInputValue(id) {
    const el = document.getElementById(id);
    return el ? el.value : null;
}

// ============================================
// Error Handling
// ============================================

function handleAPIError(error, context = '') {
    console.error(`Error in ${context}:`, error);
    showToast(`Error: ${error.message}`, 'error');
}

// ============================================
// Local Storage
// ============================================

function saveToStorage(key, value) {
    try {
        localStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('Failed to save to localStorage:', error);
    }
}

function loadFromStorage(key, defaultValue = null) {
    try {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : defaultValue;
    } catch (error) {
        console.error('Failed to load from localStorage:', error);
        return defaultValue;
    }
}

// ============================================
// Video Feed Helpers
// ============================================

function hideVideoOverlay() {
    const overlay = document.getElementById('videoOverlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

function showVideoOverlay(message) {
    const overlay = document.getElementById('videoOverlay');
    if (overlay) {
        overlay.innerHTML = `
            <div class="overlay-message">
                <span class="loader"></span>
                <p>${message}</p>
            </div>
        `;
        overlay.style.display = 'flex';
    }
}

// ============================================
// Animation Helpers
// ============================================

function animateNumber(elementId, from, to, duration = 500) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    const start = performance.now();
    const range = to - from;
    
    function update(currentTime) {
        const elapsed = currentTime - start;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function (ease-out)
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const current = from + (range * easeProgress);
        
        element.textContent = Math.round(current);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Add slide out animation
const style = document.createElement('style');
style.textContent = `
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
