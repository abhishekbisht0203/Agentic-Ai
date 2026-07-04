export interface AnalyticsSummary {
  total_conversations: number;
  total_messages: number;
  total_documents: number;
  total_knowledge_bases: number;
  total_tokens_used: number;
  total_storage_used_bytes: number;
  active_agents: number;
  active_workflows: number;
  conversations_this_week: number;
  messages_this_week: number;
  documents_this_week: number;
}

export interface AnalyticsReport {
  id: string;
  name: string;
  description: string | null;
  report_type: string;
  data: Record<string, unknown>;
  status: "pending" | "generating" | "completed" | "failed";
  created_at: string;
  updated_at: string;
}

export interface Visualization {
  id: string;
  name: string;
  description: string | null;
  chart_type: "bar" | "line" | "pie" | "area" | "scatter";
  data: Record<string, unknown>;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface UserActivity {
  id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface AnalyticsReportList {
  items: AnalyticsReport[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface VisualizationList {
  items: Visualization[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface UserActivityList {
  items: UserActivity[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AnalyticsState {
  summary: AnalyticsSummary | null;
  reports: AnalyticsReport[];
  visualizations: Visualization[];
  activities: UserActivity[];
  isLoading: boolean;
  error: string | null;
  setSummary: (summary: AnalyticsSummary) => void;
  setReports: (reports: AnalyticsReport[]) => void;
  setVisualizations: (visualizations: Visualization[]) => void;
  setActivities: (activities: UserActivity[]) => void;
  setIsLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}
