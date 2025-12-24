import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
});

// Session endpoints
export const startSession = (data) => API.post('/session/start', data);
export const stopSession = () => API.post('/session/stop');
export const getSessions = () => API.get('/sessions');
export const getSessionsList = (params) => API.get('/sessions/list', { params });
export const deleteSession = (sessionId) => API.delete(`/sessions/${sessionId}`);

// Camera/Source endpoints
export const setSource = (source) => API.post('/source', { source });
export const uploadVideo = (formData) => API.post('/upload', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
export const stopCamera = () => API.post('/camera/stop');
export const deleteUploadedVideo = () => API.post('/upload/delete');

// Playback endpoints
export const pausePlayback = () => API.post('/playback/pause');
export const resumePlayback = () => API.post('/playback/resume');
export const seekPlayback = (frame) => API.post('/playback/seek', { frame });
export const getPlaybackInfo = () => API.get('/playback/info');

// Status endpoint
export const getStatus = () => API.get('/status');

// Stats endpoint
export const getStatsOverview = () => API.get('/stats/overview');

// Defect analysis endpoints
export const analyzeDefects = (sessionId, data) => API.post(`/sessions/${sessionId}/analyze_defects`, data);
export const getSessionDefects = (sessionId) => API.get(`/sessions/${sessionId}/defects`);
export const getSessionDefectsGrouped = (sessionId) => API.get(`/sessions/${sessionId}/defects/grouped`);

export default API;
