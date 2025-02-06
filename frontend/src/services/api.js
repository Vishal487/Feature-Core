import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api/v1', // Your FastAPI backend URL
});

export const getFeatures = () => API.get('/features');
export const createFeature = (data) => API.post('/features/', data);
export const updateFeature = (id, data) => API.put(`/features/${id}`, data);