import apiClient from "./client";

export interface AdminStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  admin_users: number;
}

export interface AdminUserList {
  items: Array<{
    id: string;
    email: string;
    username: string;
    full_name: string | null;
    role: string;
    is_active: boolean;
    last_login_at: string | null;
    created_at: string;
  }>;
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const adminApi = {
  getStats: async (): Promise<AdminStats> => {
    const response = await apiClient.get<AdminStats>("/admin/stats");
    return response.data;
  },

  listUsers: async (
    page = 1,
    pageSize = 20
  ): Promise<AdminUserList> => {
    const response = await apiClient.get<AdminUserList>("/admin/users", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },
};
