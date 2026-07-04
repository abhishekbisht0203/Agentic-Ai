import apiClient from "./client";
import type {
  AgentConfiguration,
  AgentConfigurationDetail,
  AgentExecuteRequest,
  AgentExecuteResponse,
} from "@/types";

export const agentsApi = {
  listConfigurations: async (
    page = 1,
    pageSize = 100
  ): Promise<{ items: AgentConfiguration[]; total: number }> => {
    const response = await apiClient.get("/agents/configurations", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getConfiguration: async (configId: string): Promise<AgentConfigurationDetail> => {
    const response = await apiClient.get<AgentConfigurationDetail>(
      `/agents/configurations/${configId}`
    );
    return response.data;
  },

  createConfiguration: async (
    data: Omit<AgentConfiguration, "id" | "created_at" | "updated_at">
  ): Promise<AgentConfiguration> => {
    const response = await apiClient.post<AgentConfiguration>(
      "/agents/configurations",
      data
    );
    return response.data;
  },

  updateConfiguration: async (
    configId: string,
    data: Partial<AgentConfiguration>
  ): Promise<AgentConfiguration> => {
    const response = await apiClient.put<AgentConfiguration>(
      `/agents/configurations/${configId}`,
      data
    );
    return response.data;
  },

  deleteConfiguration: async (configId: string): Promise<void> => {
    await apiClient.delete(`/agents/configurations/${configId}`);
  },

  executeAgent: async (data: AgentExecuteRequest): Promise<AgentExecuteResponse> => {
    const response = await apiClient.post<AgentExecuteResponse>(
      "/agents/execute",
      data
    );
    return response.data;
  },

  getAgentStatus: async (taskId: string): Promise<AgentExecuteResponse> => {
    const response = await apiClient.get<AgentExecuteResponse>(
      `/agents/status/${taskId}`
    );
    return response.data;
  },
};
