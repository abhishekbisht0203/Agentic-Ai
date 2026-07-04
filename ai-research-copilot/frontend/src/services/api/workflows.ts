import apiClient from "./client";
import type {
  Workflow,
  WorkflowDetail,
  WorkflowExecution,
  WorkflowExecuteRequest,
} from "@/types";

export const workflowsApi = {
  listWorkflows: async (
    page = 1,
    pageSize = 20
  ): Promise<{ items: Workflow[]; total: number; page: number; page_size: number; total_pages: number }> => {
    const response = await apiClient.get("/workflows/", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getWorkflow: async (workflowId: string): Promise<WorkflowDetail> => {
    const response = await apiClient.get<WorkflowDetail>(
      `/workflows/${workflowId}`
    );
    return response.data;
  },

  createWorkflow: async (data: {
    name: string;
    description?: string;
    nodes: Workflow["nodes"];
    edges: Workflow["edges"];
    trigger_type?: string;
  }): Promise<Workflow> => {
    const response = await apiClient.post<Workflow>("/workflows/", data);
    return response.data;
  },

  updateWorkflow: async (
    workflowId: string,
    data: Partial<Workflow>
  ): Promise<Workflow> => {
    const response = await apiClient.put<Workflow>(
      `/workflows/${workflowId}`,
      data
    );
    return response.data;
  },

  deleteWorkflow: async (workflowId: string): Promise<void> => {
    await apiClient.delete(`/workflows/${workflowId}`);
  },

  executeWorkflow: async (
    workflowId: string,
    data: WorkflowExecuteRequest
  ): Promise<WorkflowExecution> => {
    const response = await apiClient.post<WorkflowExecution>(
      `/workflows/${workflowId}/execute`,
      data
    );
    return response.data;
  },

  listExecutions: async (
    workflowId: string,
    page = 1,
    pageSize = 20
  ): Promise<{ items: WorkflowExecution[]; total: number }> => {
    const response = await apiClient.get(
      `/workflows/${workflowId}/executions`,
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  getExecution: async (executionId: string): Promise<WorkflowExecution> => {
    const response = await apiClient.get<WorkflowExecution>(
      `/workflows/executions/${executionId}`
    );
    return response.data;
  },

  cancelExecution: async (executionId: string): Promise<void> => {
    await apiClient.post(`/workflows/executions/${executionId}/cancel`);
  },
};
