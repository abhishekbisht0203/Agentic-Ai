import apiClient from "./client";
import type { User } from "@/types";

export interface UserList {
  items: User[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  status: string;
  metadata: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface APIKey {
  id: string;
  name: string;
  key_prefix: string;
  permissions: string[];
  last_used_at: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface UserPreferences {
  theme: string;
  language: string;
  notifications_email: boolean;
  notifications_tasks: boolean;
  notifications_documents: boolean;
  notifications_weekly: boolean;
  compact_view: boolean;
}

export const usersApi = {
  listUsers: async (
    page = 1,
    pageSize = 20
  ): Promise<UserList> => {
    const response = await apiClient.get<UserList>("/users", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getMe: async (): Promise<User> => {
    const response = await apiClient.get<User>("/users/me");
    return response.data;
  },

  updateMe: async (data: {
    full_name?: string;
    username?: string;
  }): Promise<User> => {
    const response = await apiClient.put<User>("/users/me", data);
    return response.data;
  },

  getUser: async (userId: string): Promise<User> => {
    const response = await apiClient.get<User>(`/users/${userId}`);
    return response.data;
  },

  updateUser: async (
    userId: string,
    data: Partial<User>
  ): Promise<User> => {
    const response = await apiClient.put<User>(`/users/${userId}`, data);
    return response.data;
  },

  deleteUser: async (userId: string): Promise<void> => {
    await apiClient.delete(`/users/${userId}`);
  },

  getPreferences: async (): Promise<UserPreferences> => {
    const response = await apiClient.get<UserPreferences>("/users/me/preferences");
    return response.data;
  },

  updatePreferences: async (
    data: Partial<UserPreferences>
  ): Promise<UserPreferences> => {
    const response = await apiClient.put<UserPreferences>(
      "/users/me/preferences",
      data
    );
    return response.data;
  },

  listAPIKeys: async (): Promise<APIKey[]> => {
    const response = await apiClient.get<APIKey[]>("/users/me/api-keys");
    return response.data;
  },

  createAPIKey: async (data: {
    name: string;
    permissions: string[];
    expires_at?: string;
  }): Promise<APIKey & { key: string }> => {
    const response = await apiClient.post<APIKey & { key: string }>(
      "/users/me/api-keys",
      data
    );
    return response.data;
  },

  deleteAPIKey: async (keyId: string): Promise<void> => {
    await apiClient.delete(`/users/me/api-keys/${keyId}`);
  },

  getAuditLogs: async (
    page = 1,
    pageSize = 20
  ): Promise<{ items: AuditLog[]; total: number }> => {
    const response = await apiClient.get("/users/me/audit-logs", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },
};
