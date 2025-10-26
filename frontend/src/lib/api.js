import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      onProgress?.(percentCompleted);
    },
  });

  return response.data;
};

export const askQuestion = async (question, docIds, conversationHistory = []) => {
  const response = await api.post('/ask', {
    question,
    doc_ids: docIds,
    conversation_history: conversationHistory,
  });
  return response.data;
};

export const listDocuments = async () => {
  const response = await api.get('/documents');
  return response.data;
};

export const deleteDocument = async (docId) => {
  const response = await api.delete(`/documents/${docId}`);
  return response.data;
};

export const compareDocuments = async (docIds, question) => {
  const response = await api.post('/compare', {
    doc_ids: docIds,
    question,
  });
  return response.data;
};

export const getQuestionSuggestions = async (docId) => {
  const response = await api.get(`/suggestions/${docId}`);
  return response.data;
};

export default api;