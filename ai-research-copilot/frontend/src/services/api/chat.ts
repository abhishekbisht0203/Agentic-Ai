import apiClient from "./client";
import type {
  Conversation,
  ConversationDetail,
  Message,
  ChatRequest,
  ChatResponse,
  Bookmark,
  PaginatedList,
} from "@/types";

export const chatApi = {
  createConversation: async (data: {
    title?: string;
    agent_type?: string;
    knowledge_base_id?: string;
  }): Promise<Conversation> => {
    const response = await apiClient.post<Conversation>("/chat/conversations", data);
    return response.data;
  },

  listConversations: async (
    page = 1,
    pageSize = 20
  ): Promise<PaginatedList<Conversation>> => {
    const response = await apiClient.get<PaginatedList<Conversation>>(
      "/chat/conversations",
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  getConversation: async (convId: string): Promise<ConversationDetail> => {
    const response = await apiClient.get<ConversationDetail>(
      `/chat/conversations/${convId}`
    );
    return response.data;
  },

  updateConversation: async (
    convId: string,
    data: { title?: string; description?: string; status?: string }
  ): Promise<Conversation> => {
    const response = await apiClient.put<Conversation>(
      `/chat/conversations/${convId}`,
      data
    );
    return response.data;
  },

  deleteConversation: async (convId: string): Promise<void> => {
    await apiClient.delete(`/chat/conversations/${convId}`);
  },

  getMessages: async (
    convId: string,
    page = 1,
    pageSize = 50
  ): Promise<PaginatedList<Message>> => {
    const response = await apiClient.get<PaginatedList<Message>>(
      `/chat/conversations/${convId}/messages`,
      { params: { page, page_size: pageSize } }
    );
    return response.data;
  },

  sendMessage: async (data: ChatRequest): Promise<ChatResponse> => {
    const response = await apiClient.post<ChatResponse>("/chat/send", data);
    return response.data;
  },

  sendMessageStream: async function* (data: ChatRequest) {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

    const response = await fetch(`${API_BASE}/chat/send-stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`HTTP error: ${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) throw new Error("No response body");

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const parsed = JSON.parse(line.slice(6));
            yield parsed;
          } catch {
            // skip malformed lines
          }
        }
      }
    }
  },

  bookmarkConversation: async (data: {
    conversation_id: string;
    note?: string;
  }): Promise<Bookmark> => {
    const response = await apiClient.post<Bookmark>("/chat/bookmarks", data);
    return response.data;
  },

  listBookmarks: async (): Promise<Bookmark[]> => {
    const response = await apiClient.get<Bookmark[]>("/chat/bookmarks");
    return response.data;
  },

  deleteBookmark: async (bookmarkId: string): Promise<void> => {
    await apiClient.delete(`/chat/bookmarks/${bookmarkId}`);
  },
};
