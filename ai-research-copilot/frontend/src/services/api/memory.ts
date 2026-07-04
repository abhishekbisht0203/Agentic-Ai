import apiClient from "./client";

export interface MemoryEntry {
  id: string;
  content: string;
  category: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface MemoryList {
  items: MemoryEntry[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const memoryApi = {
  listEntries: async (
    page = 1,
    pageSize = 20
  ): Promise<MemoryList> => {
    const response = await apiClient.get<MemoryList>("/memory/entries", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  createEntry: async (data: {
    content: string;
    category?: string;
    metadata?: Record<string, unknown>;
  }): Promise<MemoryEntry> => {
    const response = await apiClient.post<MemoryEntry>("/memory/entries", data);
    return response.data;
  },

  updateEntry: async (
    entryId: string,
    data: { content?: string; category?: string; metadata?: Record<string, unknown> }
  ): Promise<MemoryEntry> => {
    const response = await apiClient.put<MemoryEntry>(
      `/memory/entries/${entryId}`,
      data
    );
    return response.data;
  },

  deleteEntry: async (entryId: string): Promise<void> => {
    await apiClient.delete(`/memory/entries/${entryId}`);
  },

  search: async (query: string, limit = 10): Promise<MemoryEntry[]> => {
    const response = await apiClient.get<MemoryEntry[]>("/memory/search", {
      params: { q: query, limit },
    });
    return response.data;
  },

  getPreferences: async (): Promise<Record<string, unknown>> => {
    const response = await apiClient.get("/memory/preferences");
    return response.data;
  },

  updatePreferences: async (
    data: Record<string, unknown>
  ): Promise<Record<string, unknown>> => {
    const response = await apiClient.put("/memory/preferences", data);
    return response.data;
  },
};
