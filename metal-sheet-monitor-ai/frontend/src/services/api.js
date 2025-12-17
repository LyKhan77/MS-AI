import axios from 'axios';

const API_URL = 'http://localhost:8000/api/v1';

const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const streamAPI = {
    setSource: (mode, path) => api.post('/streams/config', { mode, path }),
    uploadVideo: (formData) => api.post('/streams/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),
    getStatus: () => api.get('/streams/status'),
};

export const sessionAPI = {
    start: (name, target) => api.post('/sessions/start', { name, target }),
    stop: () => api.post('/sessions/stop'),
    getStatus: () => api.get('/sessions/status'),
};

export const defectAPI = {
    analyze: (imagePath) => api.post('/defects/analyze', { image_path: imagePath }),
};

export default api;
