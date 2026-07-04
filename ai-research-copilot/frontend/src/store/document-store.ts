import { create } from "zustand";
import type {
  DocumentState,
  Document,
  DocumentDetail,
  UploadItem,
} from "@/types";

export const useDocumentStore = create<DocumentState>((set, get) => ({
  documents: [],
  currentDocument: null,
  uploadQueue: [],
  isLoading: false,
  error: null,

  setDocuments: (documents: Document[]) => set({ documents }),
  setCurrentDocument: (doc: DocumentDetail | null) =>
    set({ currentDocument: doc }),

  addToUploadQueue: (item: UploadItem) =>
    set((state) => ({
      uploadQueue: [...state.uploadQueue, item],
    })),

  updateUploadProgress: (id: string, progress: number) =>
    set((state) => ({
      uploadQueue: state.uploadQueue.map((item) =>
        item.id === id ? { ...item, progress } : item
      ),
    })),

  updateUploadStatus: (
    id: string,
    status: UploadItem["status"],
    error?: string,
    documentId?: string
  ) =>
    set((state) => ({
      uploadQueue: state.uploadQueue.map((item) =>
        item.id === id ? { ...item, status, error, documentId } : item
      ),
    })),

  removeFromUploadQueue: (id: string) =>
    set((state) => ({
      uploadQueue: state.uploadQueue.filter((item) => item.id !== id),
    })),

  clearUploadQueue: () => set({ uploadQueue: [] }),

  setIsLoading: (isLoading: boolean) => set({ isLoading }),
  setError: (error: string | null) => set({ error }),
}));
