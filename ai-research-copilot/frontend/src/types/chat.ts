export interface Conversation {
  id: string;
  title: string;
  description: string | null;
  status: "active" | "archived" | "deleted";
  agent_type: string | null;
  knowledge_base_id: string | null;
  message_count: number;
  last_message_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface ConversationDetail extends Conversation {
  messages: Message[];
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  agent_type?: string;
  model?: string;
  knowledge_base_id?: string;
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  citations: Citation[];
}

export interface Citation {
  document_id: string;
  document_name: string;
  chunk_content: string;
  score: number;
  page_number?: number;
}

export interface Bookmark {
  id: string;
  conversation_id: string;
  user_id: string;
  note: string | null;
  created_at: string;
}

export interface ChatState {
  conversations: Conversation[];
  currentConversation: ConversationDetail | null;
  messages: Message[];
  isLoading: boolean;
  isStreaming: boolean;
  error: string | null;
  searchQuery: string;
  selectedConversations: string[];
  setConversations: (conversations: Conversation[]) => void;
  setCurrentConversation: (conversation: ConversationDetail | null) => void;
  addMessage: (message: Message) => void;
  setIsLoading: (isLoading: boolean) => void;
  setIsStreaming: (isStreaming: boolean) => void;
  setError: (error: string | null) => void;
  setSearchQuery: (query: string) => void;
  setSelectedConversations: (ids: string[]) => void;
  clearChat: () => void;
}

export interface PaginatedList<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
