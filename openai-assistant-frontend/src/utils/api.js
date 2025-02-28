import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const fetchDocuments = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/documents`);
    return response.data;
  } catch (error) {
    console.error('Error fetching documents:', error);
    throw error;
  }
};

export const sendMessage = async (messages, searchWeb) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/chat`, {
      messages,
      search_web: searchWeb
    });
    return response.data;
  } catch (error) {
    console.error('Error sending message:', error);
    throw error;
  }
};

export const uploadDocument = async (file, onProgressUpdate) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await axios.post(`${API_BASE_URL}/upload-document`, formData, {
      onUploadProgress: (progressEvent) => {
        // Calculate and report upload progress
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        if (onProgressUpdate) {
          onProgressUpdate(percentCompleted);
        }
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error uploading document:', error);
    throw error;
  }
};

export const deleteDocument = async (documentId) => {
  try {
    const response = await axios.delete(`${API_BASE_URL}/documents/${documentId}`);
    return response.data;
  } catch (error) {
    console.error('Error deleting document:', error);
    throw error;
  }
};

export const getVectorStoreInfo = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/vector-stores`);
    return response.data;
  } catch (error) {
    console.error('Error getting vector store info:', error);
    throw error;
  }
};

export const createVisualization = async (prompt) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/create-visualization`, { prompt });
    return response.data;
  } catch (error) {
    console.error('Error creating visualization:', error);
    throw error;
  }
};