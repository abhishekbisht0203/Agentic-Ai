import apiClient from "./client";
import type { Document } from "@/types";

export interface KnowledgeBase {
  id: string;
  name: string;
  description: string | null;
  document_count: number;
  total_chunks: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeBaseDetail extends KnowledgeBase {
  documents: Document[];
}

export interface KnowledgeBaseList {
  items: KnowledgeBase[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export const knowledgeBasesApi = {
  list: async (
    page = 1,
    pageSize = 20
  ): Promise<KnowledgeBaseList> => {
    const response = await apiClient.get<KnowledgeBaseList>("/knowledge-bases", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  get: async (kbId: string): Promise<KnowledgeBaseDetail> => {
    const response = await apiClient.get<KnowledgeBaseDetail>(
      `/knowledge-bases/${kbId}`
    );
    return response.data;
  },

  create: async (data: {
    name: string;
    description?: string;
  }): Promise<KnowledgeBase> => {
    const response = await apiClient.post<KnowledgeBase>(
      "/knowledge-bases",
      data
    );
    return response.data;
  },

  update: async (
    kbId: string,
    data: { name?: string; description?: string }
  ): Promise<KnowledgeBase> => {
    const response = await apiClient.put<KnowledgeBase>(
      `/knowledge-bases/${kbId}`,
      data
    );
    return response.data;
  },

  delete: async (kbId: string): Promise<void> => {
    await apiClient.delete(`/knowledge-bases/${kbId}`);
  },

  addDocuments: async (
    kbId: string,
    documentIds: string[]
  ): Promise<void> => {
    await apiClient.post(`/knowledge-bases/${kbId}/documents`, {
      document_ids: documentIds,
    });
  },

  removeDocument: async (
    kbId: string,
    documentId: string
  ): Promise<void> => {
    await apiClient.delete(`/knowledge-bases/${kbId}/documents/${documentId}`);
  },
};
