import axios from 'axios';

// Extract API base URL from environment variables or default to '/api'
let rawBase = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '';

let getBaseUrl = () => {
  if (!rawBase) return '/api';
  let clean = rawBase.replace(/\/+$/, '');
  if (!clean.endsWith('/api')) {
    clean = `${clean}/api`;
  }
  return clean;
};

export const API_BASE_URL = getBaseUrl();

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: Sanitize duplicate /api/ prefix & Attach Authorization Bearer token
apiClient.interceptors.request.use(
  (config) => {
    // If the request URL starts with '/api/', strip the leading '/api' so it doesn't double up with baseURL ending in '/api'
    if (config.url && config.url.startsWith('/api/')) {
      config.url = config.url.replace(/^\/api/, '');
    }
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

