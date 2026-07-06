import apiClient from "./client";
import type {
  Document,
  DocumentDetail,
  DocumentChunk,
  DocumentUploadResponse,
  DocumentList,
} from "@/types";

export const documentsApi = {
  uploadDocument: async (
    file: File,
    name?: string,
    knowledgeBaseIds?: string[],
    conversationId?: string
  ): Promise<DocumentUploadResponse> => {
    const formData = new FormData();
    formData.append("file", file);
    if (name) formData.append("name", name);
    if (knowledgeBaseIds?.length) {
      formData.append("knowledge_base_ids", knowledgeBaseIds.join(","));
    }
    if (conversationId) {
      formData.append("conversation_id", conversationId);
    }

    const response = await apiClient.post<DocumentUploadResponse>(
      "/documents/upload",
      formData,
      {
        headers: { "Content-Type": "multipart/form-data" },
      }
    );
    return response.data;
  },

  listDocuments: async (
    page = 1,
    pageSize = 20
  ): Promise<DocumentList> => {
    const response = await apiClient.get<DocumentList>("/documents/", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  getDocument: async (documentId: string): Promise<DocumentDetail> => {
    const response = await apiClient.get<DocumentDetail>(
      `/documents/${documentId}`
    );
    return response.data;
  },

  updateDocument: async (
    documentId: string,
    data: { name?: string; metadata?: Record<string, unknown> }
  ): Promise<Document> => {
    const response = await apiClient.put<Document>(
      `/documents/${documentId}`,
      data
    );
    return response.data;
  },

  deleteDocument: async (documentId: string): Promise<void> => {
    await apiClient.delete(`/documents/${documentId}`);
  },

  getDocumentChunks: async (documentId: string): Promise<DocumentChunk[]> => {
    const response = await apiClient.get<DocumentChunk[]>(
      `/documents/${documentId}/chunks`
    );
    return response.data;
  },

  downloadDocument: async (documentId: string): Promise<Blob> => {
    const response = await apiClient.get(`/documents/${documentId}/download`, {
      responseType: "blob",
    });
    return response.data;
  },
};
