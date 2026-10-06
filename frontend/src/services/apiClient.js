import axios from 'axios';
const resolveApiBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_URL || import.meta.env.VITE_API_BASE_URL;
  if (envUrl) {
    const trimmed = envUrl.trim().replace(/\/+$/, '');
    return trimmed.endsWith('/api') ? trimmed : `${trimmed}/api`;
  }
  return import.meta.env.DEV ? 'http://localhost:8000/api' : '/api';
};

const API_BASE_URL = resolveApiBaseUrl();

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to attach Bearer Token from localStorage
apiClient.interceptors.request.use(
  (config) => {
    try {
      const token = localStorage.getItem('studypilot_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      console.error('Error reading auth token:', e);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor for Error Normalization
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    let normalizedError = {
      status: error.response?.status || 500,
      message: 'An unexpected error occurred. Please try again.',
      detail: error.response?.data?.detail || null,
      errorType: error.response?.data?.error_type || 'UnknownError',
    };

    if (error.response) {
      switch (error.response.status) {
        case 401:
          normalizedError.message = 'Session expired. Please log in again.';
          break;
        case 403:
          normalizedError.message = 'Access denied. You do not have permission for this action.';
          break;
        case 404:
          normalizedError.message = error.response.data?.detail || 'Requested resource not found.';
          break;
        case 422:
          normalizedError.message = 'Invalid data submitted. Please check input fields.';
          break;
        case 429:
          normalizedError.message = 'AI generation rate limit reached. Please wait a moment.';
          break;
        case 500:
          normalizedError.message = error.response.data?.detail || 'Server error. Please try again later.';
          break;
        default:
          normalizedError.message = error.response.data?.detail || normalizedError.message;
      }
    } else if (error.request) {
      normalizedError.message = 'Network error. Cannot reach StudyPilot server.';
    }

    return Promise.reject(normalizedError);
  }
);
