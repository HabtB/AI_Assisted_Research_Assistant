import { apiClient } from './api';
import type {
  ResearchRequest,
  ResearchResponse,
  ResearchCreateResponse,
  ResearchListResponse,
  ResearchStatusResponse,
} from '../types/api'; // This is the right path to types

export const researchApi = {
  // Start new research
  startResearch: async (data: ResearchRequest): Promise<ResearchCreateResponse> => {
    const response = await apiClient.post('/research/start', data);
    return response.data;
  },

  // Get research by ID
  getResearch: async (id: number): Promise<ResearchResponse> => {
    const response = await apiClient.get(`/research/${id}`);
    return response.data;
  },

  // Get research status
  getResearchStatus: async (id: number): Promise<ResearchStatusResponse> => {
    const response = await apiClient.get(`/research/${id}/status`);
    return response.data;
  },

  // List all research
  listResearch: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
  }): Promise<ResearchListResponse> => {
    const response = await apiClient.get('/research/', { params });
    return response.data;
  },

  // Delete research
  deleteResearch: async (id: number): Promise<{ message: string }> => {
    const response = await apiClient.delete(`/research/${id}`);
    return response.data;
  },
};