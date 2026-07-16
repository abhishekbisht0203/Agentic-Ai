import apiClient from "./client";
import type {
  AgentList,
  AgentWithStats,
  Agent,
  AgentCreate,
  AgentUpdate,
  AgentRunList,
  AgentMemory,
  AgentTool,
  AgentChatResponse,
  ProviderInfo,
  ToolInfo,
} from "@/types/agent-platform";

export const agentPlatformApi = {
  listAgents: async (params?: { page?: number; page_size?: number; search?: string }): Promise<AgentList> => {
    const response = await apiClient.get<AgentList>("/agent-platform/agents", { params });
    return response.data;
  },

  getAgent: async (agentId: string): Promise<AgentWithStats> => {
    const response = await apiClient.get<AgentWithStats>(`/agent-platform/agents/${agentId}`);
    return response.data;
  },

  createAgent: async (data: AgentCreate): Promise<Agent> => {
    const response = await apiClient.post<Agent>("/agent-platform/agents", data);
    return response.data;
  },

  updateAgent: async (agentId: string, data: AgentUpdate): Promise<Agent> => {
    const response = await apiClient.patch<Agent>(`/agent-platform/agents/${agentId}`, data);
    return response.data;
  },

  deleteAgent: async (agentId: string): Promise<void> => {
    await apiClient.delete(`/agent-platform/agents/${agentId}`);
  },

  duplicateAgent: async (agentId: string, name?: string): Promise<Agent> => {
    const response = await apiClient.post<Agent>(`/agent-platform/agents/${agentId}/duplicate`, { name });
    return response.data;
  },

  toggleAgent: async (agentId: string): Promise<Agent> => {
    const response = await apiClient.post<Agent>(`/agent-platform/agents/${agentId}/toggle`);
    return response.data;
  },

  getAgentRuns: async (agentId: string, params?: { page?: number; page_size?: number }): Promise<AgentRunList> => {
    const response = await apiClient.get<AgentRunList>(`/agent-platform/agents/${agentId}/runs`, { params });
    return response.data;
  },

  getAgentMemory: async (agentId: string): Promise<AgentMemory[]> => {
    const response = await apiClient.get<AgentMemory[]>(`/agent-platform/agents/${agentId}/memory`);
    return response.data;
  },

  addAgentMemory: async (agentId: string, key: string, value: string, memory_type = "fact"): Promise<AgentMemory> => {
    const response = await apiClient.post<AgentMemory>(`/agent-platform/agents/${agentId}/memory`, null, {
      params: { key, value, memory_type },
    });
    return response.data;
  },

  deleteAgentMemory: async (agentId: string, memoryId: string): Promise<void> => {
    await apiClient.delete(`/agent-platform/agents/${agentId}/memory/${memoryId}`);
  },

  getAgentTools: async (agentId: string): Promise<AgentTool[]> => {
    const response = await apiClient.get<AgentTool[]>(`/agent-platform/agents/${agentId}/tools`);
    return response.data;
  },

  setAgentTool: async (agentId: string, toolName: string, enabled: boolean): Promise<AgentTool> => {
    const response = await apiClient.post<AgentTool>(`/agent-platform/agents/${agentId}/tools`, null, {
      params: { tool_name: toolName, enabled },
    });
    return response.data;
  },

  sendChatMessage: async (agentId: string, data: { message: string; conversation_id?: string }): Promise<AgentChatResponse> => {
    const response = await apiClient.post<AgentChatResponse>(`/agent-platform/agents/${agentId}/chat`, data);
    return response.data;
  },

  getProviders: async (): Promise<ProviderInfo[]> => {
    const response = await apiClient.get<ProviderInfo[]>("/agent-platform/providers");
    return response.data;
  },

  getTools: async (): Promise<ToolInfo[]> => {
    const response = await apiClient.get<ToolInfo[]>("/agent-platform/tools");
    return response.data;
  },
};
