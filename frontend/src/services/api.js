import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
});

export const fetchAllFeatures = async () => {
  const response = await API.get('/features');
  return response.data;
};

export const updateFeature = async (featureId, payload) => {
  const response = await API.put(`/features/${featureId}`, payload);
  return response.data;
};

export const createFeature = async (payload) => {
  const response = await API.post('/features/', payload);
  return response.data;
};

export const deleteFeature = async (featureId) => {
  const response = await API.delete(`/features/${featureId}`);
  return response.data;
};
