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
