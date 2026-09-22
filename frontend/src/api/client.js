import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '/api';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Attach Authorization Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('oil_auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: Standard error response extraction & HTML fallback detection
apiClient.interceptors.response.use(
  (response) => {
    // Detect HTML fallback response (e.g. index.html returned by static server when API URL is misconfigured)
    if (typeof response.data === 'string' && (response.data.includes('<!DOCTYPE html>') || response.data.includes('<html'))) {
      const err = new Error('Server returned HTML instead of API JSON response. Please ensure VITE_API_BASE_URL points to the backend API.');
      err.status = 502;
      return Promise.reject(err);
    }
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('oil_auth_token');
      localStorage.removeItem('oil_user_data');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login?expired=true';
      }
    }
    const message = error.response?.data?.message || error.message || 'An unexpected error occurred';
    return Promise.reject(new Error(message));
  }
);
