import apiClient from "./client";

export interface Task {
  id: string;
  task_type: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface TaskList {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const tasksApi = {
  create: async (data: {
    task_type: string;
    input_data: Record<string, unknown>;
  }): Promise<Task> => {
    const response = await apiClient.post<Task>("/tasks", data);
    return response.data;
  },

  list: async (
    page = 1,
    pageSize = 20
  ): Promise<TaskList> => {
    const response = await apiClient.get<TaskList>("/tasks", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  get: async (taskId: string): Promise<Task> => {
    const response = await apiClient.get<Task>(`/tasks/${taskId}`);
    return response.data;
  },

  cancel: async (taskId: string): Promise<void> => {
    await apiClient.post(`/tasks/${taskId}/cancel`);
  },
};
