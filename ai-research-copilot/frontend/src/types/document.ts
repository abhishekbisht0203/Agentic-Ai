export interface Document {
  id: string;
  name: string;
  original_filename: string;
  mime_type: string;
  file_size: number;
  status: "pending" | "processing" | "completed" | "failed";
  chunk_count: number;
  embedding_status: "pending" | "processing" | "completed" | "failed";
  error_message: string | null;
  metadata: Record<string, unknown> | null;
  knowledge_base_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface DocumentDetail extends Document {
  chunks: DocumentChunk[];
}

export interface DocumentChunk {
  id: string;
  document_id: string;
  content: string;
  chunk_index: number;
  token_count: number;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface DocumentUploadResponse {
  id: string;
  name: string;
  status: string;
  message: string;
}

export interface DocumentList {
  items: Document[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DocumentState {
  documents: Document[];
  currentDocument: DocumentDetail | null;
  uploadQueue: UploadItem[];
  isLoading: boolean;
  error: string | null;
  setDocuments: (documents: Document[]) => void;
  setCurrentDocument: (doc: DocumentDetail | null) => void;
  addToUploadQueue: (item: UploadItem) => void;
  updateUploadProgress: (id: string, progress: number) => void;
  updateUploadStatus: (
    id: string,
    status: UploadItem["status"],
    error?: string,
    documentId?: string
  ) => void;
  removeFromUploadQueue: (id: string) => void;
  clearUploadQueue: () => void;
  setIsLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}

export interface UploadItem {
  id: string;
  file: File;
  progress: number;
  status: "pending" | "uploading" | "completed" | "error";
  error?: string;
  documentId?: string;
}
