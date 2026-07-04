import { create } from "zustand";
import type { ChatState, Message, Conversation, ConversationDetail } from "@/types";

export const useChatStore = create<ChatState>((set) => ({
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
    }),
}));
