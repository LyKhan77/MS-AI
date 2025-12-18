/**
 * API Communication Module
 * Handles all HTTP requests to backend API
 */

const API = {
    baseURL: '',
    
    /**
     * Generic fetch wrapper with error handling
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };
        
        try {
            const response = await fetch(url, config);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error(`API Error [${endpoint}]:`, error);
            throw error;
        }
    },
    
    // ============================================
    // Session Management
    // ============================================
    
    async startSession(sessionName, maxCountTarget) {
        return this.request('/api/session/start', {
            method: 'POST',
            body: JSON.stringify({
                session_name: sessionName,
                max_count_target: maxCountTarget
            })
        });
    },
    
    async finishSession() {
        return this.request('/api/session/finish', {
            method: 'POST'
        });
    },
    
    async getSessionStatus() {
        return this.request('/api/session/status');
    },
    
    // ============================================
    // Camera Control
    // ============================================
    
    async setRTSP(rtspUrl) {
        return this.request('/api/camera/set_rtsp', {
            method: 'POST',
            body: JSON.stringify({
                rtsp_url: rtspUrl
            })
        });
    },
    
    async uploadVideo(formData) {
        // Override default headers for multipart/form-data
        return this.request('/api/camera/upload_video', {
            method: 'POST',
            headers: {},  // Let browser set Content-Type with boundary
            body: formData
        });
    },
    
    // ============================================
    // System Status
    // ============================================
    
    async getSystemHealth() {
        return this.request('/api/system/health');
    },
    
    async listSessions() {
        return this.request('/api/sessions/list');
    },
    
    async getSessionDetails(sessionId) {
        return this.request(`/api/sessions/${sessionId}/details`);
    }
};
