import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Attach Authorization Bearer token to outgoing requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('jansethu_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Intercept responses for token refresh / clearance and user-friendly error formatting
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('jansethu_token');
      localStorage.removeItem('jansethu_user');
    }
    
    // Standardize error message extraction
    const serverError = error.response?.data?.error;
    const detailObj = error.response?.data?.detail;
    const detailMessage = typeof detailObj === 'string' ? detailObj : (detailObj?.message || detailObj?.code);
    const userMessage = serverError?.message 
      || detailMessage 
      || (error.code === 'ERR_NETWORK' 
          ? 'Unable to reach JanSethu servers. Please check your network connection.' 
          : 'An unexpected error occurred. Please try again.');
          
    const customError = new Error(userMessage);
    customError.code = serverError?.code || detailObj?.code || error.code || 'UNKNOWN_ERROR';
    customError.status = error.response?.status || 500;
    customError.response = error.response;
    customError.originalError = error;
    
    return Promise.reject(customError);
  }
);

export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error("Health check error:", error);
    return {
      status: 'offline',
      service: 'JanSethu AI 2.0 Backend',
      database: 'disconnected',
      error: error.message || 'Server unreachable'
    };
  }
};

