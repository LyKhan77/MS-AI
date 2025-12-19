import axios from 'axios';

const API = axios.create({
  baseURL: '/api',
});

export const startSession = (data) => API.post('/session/start', data);
export const stopSession = () => API.post('/session/stop');
export const getSessions = () => API.get('/sessions');
export const setSource = (source) => API.post('/source', { source });
export const getStatus = () => API.get('/status');

export default API;
