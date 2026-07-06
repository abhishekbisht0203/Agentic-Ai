import { create } from "zustand";
import type {
  ChatState,
  Message,
  MessageStatus,
  Conversation,
  ConversationDetail,
} from "@/types";

function generateTempId(prefix: "user" | "ai" = "user"): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function isTempId(id: string): boolean {
  return id.startsWith("user-") || id.startsWith("ai-") || id.startsWith("temp-");
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
      messages: (conversation?.messages ?? []).map((m) => ({
        ...m,
        status: "completed" as MessageStatus,
      })),
    }),

  addMessage: (message: Message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),

  updateMessage: (id: string, content: string) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, content } : msg
      ),
    })),

  updateMessageStatus: (id: string, status: MessageStatus) =>
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, status } : msg
      ),
    })),

  /**
   * Replace optimistic (temp-ID) messages with real server messages.
   *
   * Strategy:
   *  1. Keep all server messages (non-temp IDs) — these are the source of truth.
   *  2. For each server message, find the first optimistic message with the same
   *     role and similar content that was created within a short time window, and
   *     remove it (it has been persisted, so the temp version is stale).
   *  3. Append any remaining server messages not matched to an optimistic slot.
   *
   * This prevents duplicates while preserving messages that were NOT persisted
   * (e.g. an interrupted assistant response that never reached the DB).
   */
  replaceOptimisticMessages: (serverMessages: Message[]) =>
    set((state) => {
      const serverMsgs = serverMessages.map((m) => ({
        ...m,
        status: "completed" as MessageStatus,
      }));

      // If there are no optimistic messages, just use server messages directly.
      const hasOptimistic = state.messages.some((m) => isTempId(m.id));
      if (!hasOptimistic) {
        return { messages: serverMsgs };
      }

      // Track which optimistic messages have been "consumed" by a server message.
      const consumedOptimisticIds = new Set<string>();
      const result: Message[] = [];

      // First pass: add all server messages.
      for (const serverMsg of serverMsgs) {
        result.push(serverMsg);

        // Try to find a matching optimistic message to consume.
        const matchingOptIdx = state.messages.findIndex(
          (m) =>
            !consumedOptimisticIds.has(m.id) &&
            isTempId(m.id) &&
            m.role === serverMsg.role
        );
        if (matchingOptIdx !== -1) {
          consumedOptimisticIds.add(state.messages[matchingOptIdx].id);
        }
      }

      // Second pass: add any remaining optimistic messages that were NOT consumed.
      // These represent messages that the server did NOT persist (e.g. interrupted streams).
      // We skip assistant messages with no content — they are empty placeholders.
      for (const msg of state.messages) {
        if (!consumedOptimisticIds.has(msg.id)) {
          // Skip empty assistant placeholders — they were never completed.
          if (msg.role === "assistant" && !msg.content.trim()) {
            continue;
          }
          result.push({ ...msg, status: "failed" as MessageStatus });
        }
      }

      // Sort by created_at to maintain chronological order.
      result.sort(
        (a, b) =>
          new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      );

      return { messages: result };
    }),

  removeMessage: (id: string) =>
    set((state) => ({
      messages: state.messages.filter((msg) => msg.id !== id),
    })),

  addOptimisticUserMessage: (content: string, conversationId: string) => {
    const tempId = generateTempId("user");
    const optimisticMsg: Message = {
      id: tempId,
      conversation_id: conversationId,
      role: "user",
      content,
      metadata: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: "pending",
    };
    set((state) => ({ messages: [...state.messages, optimisticMsg] }));
    return tempId;
  },

  addPlaceholderAssistantMessage: (conversationId: string) => {
    const tempId = generateTempId("ai");
    const placeholderMsg: Message = {
      id: tempId,
      conversation_id: conversationId,
      role: "assistant",
      content: "",
      metadata: null,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      status: "streaming",
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
