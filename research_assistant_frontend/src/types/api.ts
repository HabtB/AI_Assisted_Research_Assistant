// Enums matching backend
export type ResearchStatus = "pending" | "in_progress" | "completed" | "failed";

export type SourceType = "web" | "academic" | "news" | "api";

// Request types
export interface ResearchRequest {
  query: string;
  max_results?: number;
  include_summary?: boolean;
  language?: string;
  source_types?: SourceType[];
}

// Response types
export interface ResearchResponse {
  id: number;
  query: string;
  status: ResearchStatus;
  created_at: string;
  completed_at?: string;
  max_results: number;
  include_summary: boolean;
  language: string;
  summary?: string;
  key_findings?: string[];
  error_message?: string;
  sources: SourceResponse[];
}

export interface SourceResponse {
  id: number;
  title: string;
  url: string;
  snippet?: string;
  source_type: string;
  credibility_score: number;
  relevance_score: number;
  published_date?: string;
  author?: string;
}

export interface ResearchCreateResponse {
  success: boolean;
  message: string;
  research: ResearchResponse;
}

export interface ResearchListResponse {
  success: boolean;
  message: string;
  research_list: ResearchSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface ResearchSummary {
  id: number;
  query: string;
  status: ResearchStatus;
  created_at: string;
  completed_at?: string;
  source_count: number;
}

export interface TaskInfo {
  task_id: string;
  task_status: string;
  task_info: unknown;
}

export interface ResearchStatusResponse {
  research_id: number;
  status: ResearchStatus;
  created_at: string;
  completed_at?: string;
  task_info?: TaskInfo;
  error_message?: string;
}