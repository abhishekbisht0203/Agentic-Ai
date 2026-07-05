import { create } from "zustand";
import type { ChatState, Message, Conversation, ConversationDetail } from "@/types";

function generateTempId(): string {
  return `temp-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  isStreaming: false,
  error: null,
  searchQuery: "",
  selectedConversations: [],

  setConversations: (conversations: Conversation[]) => set({ conversations }),
  setCurrentConversation: (conversation: ConversationDetail | null) =>
    set({
      currentConversation: conversation,
      messages: conversation?.messages ?? [],
    }),
  addMessage: (message: Message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  updateMessage: (id: string, content: string) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content } : msg
      ),
    })),
  addOptimisticUserMessage: (content: string, conversationId: string) => {
    const tempId = generateTempId();
    const optimisticMsg: Message = {
      id: tempId,
      conversation_id: conversationId,
      role: "user",
      content,
      metadata: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    set((state) => ({ messages: [...state.messages, optimisticMsg] }));
    return tempId;
  },
  addPlaceholderAssistantMessage: (conversationId: string) => {
    const tempId = generateTempId();
    const placeholderMsg: Message = {
      id: tempId,
      conversation_id: conversationId,
      role: "assistant",
      content: "",
      metadata: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };
    set((state) => ({ messages: [...state.messages, placeholderMsg] }));
    return tempId;
  },
  setIsLoading: (isLoading: boolean) => set({ isLoading }),
  setIsStreaming: (isStreaming: boolean) => set({ isStreaming }),
  setError: (error: string | null) => set({ error }),
  setSearchQuery: (query: string) => set({ searchQuery: query }),
  setSelectedConversations: (ids: string[]) =>
    set({ selectedConversations: ids }),
  clearChat: () =>
    set({
      currentConversation: null,
      messages: [],
      error: null,
      isStreaming: false,
      isLoading: false,
    }),
}));
