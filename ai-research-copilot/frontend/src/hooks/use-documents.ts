"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useDocumentStore } from "@/store/document-store";
import { documentsApi } from "@/services/api/documents";
import { generateId } from "@/utils/helpers";
import type { UploadItem } from "@/types";

export function useDocuments() {
  const queryClient = useQueryClient();
  const store = useDocumentStore();

  const { data, isLoading } = useQuery({
    queryKey: ["documents"],
    queryFn: () => documentsApi.listDocuments(),
  });

  const uploadMutation = useMutation({
    mutationFn: async ({ file, name, knowledgeBaseIds }: {
      file: File;
      name?: string;
      knowledgeBaseIds?: string[];
    }) => {
      const uploadItem: UploadItem = {
        id: generateId(),
        file,
        progress: 0,
        status: "uploading",
      };
      store.addToUploadQueue(uploadItem);

      try {
        store.updateUploadProgress(uploadItem.id, 50);
        const result = await documentsApi.uploadDocument(file, name, knowledgeBaseIds);
        store.updateUploadStatus(uploadItem.id, "completed", undefined, result.id);
        return result;
      } catch (error) {
        const message = error instanceof Error ? error.message : "Upload failed";
        store.updateUploadStatus(uploadItem.id, "error", message);
        throw error;
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const deleteDocument = useMutation({
    mutationFn: (id: string) => documentsApi.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const downloadDocument = useMutation({
    mutationFn: async (id: string) => {
      const blob = await documentsApi.downloadDocument(id);
      const doc = data?.items.find((d) => d.id === id);
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement("a");
      a.href = url;
      a.download = doc?.original_filename || "document";
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);
    },
  });

  return {
    documents: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    error: store.error,
    uploadQueue: store.uploadQueue,
    uploadDocument: uploadMutation,
    deleteDocument,
    downloadDocument,
    clearUploadQueue: store.clearUploadQueue,
    removeFromUploadQueue: store.removeFromUploadQueue,
  };
}
