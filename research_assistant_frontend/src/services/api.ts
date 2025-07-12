import axios from "axios";
import type { AxiosInstance, AxiosError } from "axios"; // <-- Use 'type' for type-only imports

const API_PREFIX = '/api/v1';  // Relative path; Vite proxies '/api' to backend

// Create axios instance with default config
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_PREFIX,  // Now relative; assumes Vite proxy setup
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token here if needed in future
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // Request made but no response (e.g., CORS/network)
      console.error('Network Error:', error.message);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Error type
export interface ApiError {
  message: string;
  status?: number;
  details?: unknown;
}

// Helper for starting research (ensures valid payload)
export async function startResearch(payload: any) {
  // Fallback defaults to avoid validation errors
  payload.source_types = payload.source_types || ['academic'];
  payload.max_results = payload.max_results || 20;
  payload.include_summary = payload.include_summary ?? true;
  payload.language = payload.language || 'en';

  return apiClient.post('/research/start', payload);
}

// Add other API helpers as needed, e.g., getResearch(id) { return apiClient.get(`/research/${id}`); }