import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '../services/api.ts';  // Adjust path if needed

// Existing hooks...
export const useStartResearch = () => {
  return useMutation({
    mutationFn: async (payload: any) => {
      const { data } = await apiClient.post('/research/start', payload);
      return data;
    },
  });
};

export const useResearchStatus = (id: number | null) => {
  return useQuery({
    queryKey: ['researchStatus', id],
    queryFn: async () => {
      if (!id) throw new Error('No ID');
      const { data } = await apiClient.get(`/research/${id}/status`);
      return data;
    },
    enabled: !!id,
    refetchInterval: 5000,  // Poll for updates
  });
};

export const useResearchList = () => {
  return useQuery({
    queryKey: ['researchList'],
    queryFn: async () => {
      const { data } = await apiClient.get('/research/');
      return data;
    },
    refetchInterval: 10000,  // Refresh list periodically
  });
};

// New hook for fetching full research details
export const useResearchDetails = (id: number | null) => {
  return useQuery({
    queryKey: ['researchDetails', id],
    queryFn: async () => {
      if (!id) throw new Error('No ID provided');
      const { data } = await apiClient.get(`/research/${id}`);
      return data;
    },
    enabled: !!id,
    refetchInterval: (query) => (query.state.data?.status === 'processing' ? 5000 : false),  // Poll only if processing
  });
};

// Hook for getting enhanced research summary
export const useResearchSummary = (id: number | null) => {
  return useQuery({
    queryKey: ['researchSummary', id],
    queryFn: async () => {
      if (!id) throw new Error('No ID provided');
      const { data } = await apiClient.get(`/research/${id}/summary`);
      return data;
    },
    enabled: !!id,
  });
};

// Hook for filtering research results
export const useFilteredResearch = () => {
  return useMutation({
    mutationFn: async ({
      id,
      filters
    }: {
      id: number;
      filters: {
        year_from?: number;
        year_to?: number;
        min_citations?: number;
        venues?: string;
        has_pdf?: boolean;
      };
    }) => {
      const params = new URLSearchParams();
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          params.append(key, value.toString());
        }
      });
      
      const { data } = await apiClient.get(`/research/${id}/filter?${params}`);
      return data;
    },
  });
};

// Hook for exporting research results
export const useExportResearch = () => {
  return useMutation({
    mutationFn: async ({
      id,
      format
    }: {
      id: number;
      format: 'csv' | 'json' | 'excel' | 'bibtex';
    }) => {
      const response = await apiClient.get(`/research/${id}/export?format=${format}`, {
        responseType: 'blob',
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `research_${id}_results.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      return { success: true, format };
    },
  });
};