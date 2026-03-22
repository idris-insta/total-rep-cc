/**
 * API Service Configuration
 * Centralized API client with interceptors
 */
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '';

// Create axios instance with default config (legacy routes)
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Create V1 axios instance (new layered architecture routes)
export const v1Api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Add interceptors to an axios instance
const addInterceptors = (instance) => {
  // Request interceptor - add auth token
  instance.interceptors.request.use(
    (config) => {
      const token = localStorage.getItem('token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor - handle errors
  instance.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
      return Promise.reject(error);
    }
  );
};

// Apply interceptors to both instances
addInterceptors(apiClient);
addInterceptors(v1Api);

export default apiClient;

// Helper functions
export const setAuthToken = (token) => {
  localStorage.setItem('token', token);
};

export const clearAuthToken = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
};

export const getAuthToken = () => {
  return localStorage.getItem('token');
};
