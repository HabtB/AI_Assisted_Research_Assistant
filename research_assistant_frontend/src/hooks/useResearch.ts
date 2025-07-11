import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { researchApi } from '../services/research';
import type { ResearchRequest, ResearchStatusResponse, ResearchListResponse } from '../types/api';

// Hook to start new research
export const useStartResearch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: ResearchRequest) => researchApi.startResearch(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research'] });
    },
  });
};

// Hook to get research by ID
export const useResearch = (id: number | null) => {
  return useQuery({
    queryKey: ['research', id],
    queryFn: () => researchApi.getResearch(id!),
    enabled: !!id,
  });
};

// Hook to get research status with polling
export const useResearchStatus = (id: number | null, enabled: boolean = true) => {
  return useQuery<ResearchStatusResponse>({
    queryKey: ['research-status', id],
    queryFn: () => researchApi.getResearchStatus(id!),
    enabled: !!id && enabled,
    refetchInterval: (query: unknown) => {
      const lastData = (query as { data?: ResearchStatusResponse }).data;
      if (lastData?.status === "pending" || lastData?.status === "in_progress") {
        return 2000; // Poll every 2 seconds
      }
      return false; // Stop polling
    },
  });
};

// Hook to list research
export const useResearchList = (params?: {
  page?: number;
  page_size?: number;
  status?: string;
}) => {
  return useQuery<ResearchListResponse>({
    queryKey: ['research', 'list', params],
    queryFn: () => researchApi.listResearch(params),
  });
};

// Hook to delete research
export const useDeleteResearch = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => researchApi.deleteResearch(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research'] });
    },
  });
};