import apiClient from "./client";
import type {
  AnalyticsSummary,
  AnalyticsReport,
  AnalyticsReportList,
  Visualization,
  VisualizationList,
  UserActivityList,
} from "@/types";

export const analyticsApi = {
  getSummary: async (): Promise<AnalyticsSummary> => {
    const response = await apiClient.get<AnalyticsSummary>("/analytics/summary");
    return response.data;
  },

  listReports: async (
    page = 1,
    pageSize = 20
  ): Promise<AnalyticsReportList> => {
    const response = await apiClient.get<AnalyticsReportList>("/analytics/reports", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getReport: async (reportId: string): Promise<AnalyticsReport> => {
    const response = await apiClient.get<AnalyticsReport>(
      `/analytics/reports/${reportId}`
    );
    return response.data;
  },

  createReport: async (data: {
    name: string;
    description?: string;
    report_type: string;
  }): Promise<AnalyticsReport> => {
    const response = await apiClient.post<AnalyticsReport>(
      "/analytics/reports",
      data
    );
    return response.data;
  },

  deleteReport: async (reportId: string): Promise<void> => {
    await apiClient.delete(`/analytics/reports/${reportId}`);
  },

  listVisualizations: async (
    page = 1,
    pageSize = 20
  ): Promise<VisualizationList> => {
    const response = await apiClient.get<VisualizationList>(
      "/analytics/visualizations",
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  getVisualization: async (vizId: string): Promise<Visualization> => {
    const response = await apiClient.get<Visualization>(
      `/analytics/visualizations/${vizId}`
    );
    return response.data;
  },

  createVisualization: async (data: {
    name: string;
    description?: string;
    chart_type: string;
    data: Record<string, unknown>;
    config?: Record<string, unknown>;
  }): Promise<Visualization> => {
    const response = await apiClient.post<Visualization>(
      "/analytics/visualizations",
      data
    );
    return response.data;
  },

  deleteVisualization: async (vizId: string): Promise<void> => {
    await apiClient.delete(`/analytics/visualizations/${vizId}`);
  },

  getUserActivity: async (
    page = 1,
    pageSize = 20
  ): Promise<UserActivityList> => {
    const response = await apiClient.get<UserActivityList>(
      "/analytics/activity",
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  getTokenUsage: async (days = 30): Promise<{ summary: { total_requests: number; total_tokens: number; total_cost: number; avg_duration_ms: number; prompt_tokens: number; completion_tokens: number }; trend: Array<{ date: string; prompt_tokens: number; completion_tokens: number; requests: number }> }> => {
    const response = await apiClient.get("/analytics/usage/tokens", { params: { days } });
    return response.data;
  },

  getCostAnalytics: async (): Promise<{ breakdown: Array<{ provider: string; model: string; cost: number; requests: number; tokens: number }>; total_cost: number }> => {
    const response = await apiClient.get("/analytics/usage/costs");
    return response.data;
  },

  getModelPerformance: async (): Promise<{ models: Array<{ provider: string; model: string; requests: number; avg_duration_ms: number; total_tokens: number; cost: number }> }> => {
    const response = await apiClient.get("/analytics/usage/models");
    return response.data;
  },

  getErrorAnalytics: async (): Promise<{ total: number; failed: number; error_rate: number }> => {
    const response = await apiClient.get("/analytics/usage/errors");
    return response.data;
  },

  getDashboardUsage: async (): Promise<{
    total_requests: number;
    today_requests: number;
    weekly_requests: number;
    monthly_requests: number;
    total_tokens: number;
    prompt_tokens: number;
    completion_tokens: number;
    total_cost: number;
    today_cost: number;
    weekly_cost: number;
    monthly_cost: number;
    failed_requests: number;
    streaming_requests: number;
    cached_requests: number;
    avg_duration_ms: number;
    avg_cost_per_conversation: number;
  }> => {
    const response = await apiClient.get("/analytics/usage/dashboard");
    return response.data;
  },

  getStorageUsage: async (): Promise<{
    total_storage_bytes: number;
    total_documents: number;
    uploaded_today: number;
  }> => {
    const response = await apiClient.get("/analytics/usage/storage");
    return response.data;
  },
};
