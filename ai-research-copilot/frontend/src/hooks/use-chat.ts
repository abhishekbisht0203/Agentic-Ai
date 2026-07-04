"use client";

import { useCallback } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useChatStore } from "@/store/chat-store";
import { chatApi } from "@/services/api/chat";
import type { ChatRequest } from "@/types";

export function useChat() {
  const queryClient = useQueryClient();
  const store = useChatStore();

  const { data: conversationsData, isLoading: isLoadingConversations } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => chatApi.listConversations(),
  });

  const createConversation = useMutation({
    mutationFn: (data: { title?: string; agent_type?: string; knowledge_base_id?: string }) =>
      chatApi.createConversation(data),
    onSuccess: (newConv) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      store.setCurrentConversation({ ...newConv, messages: [] });
      return newConv;
    },
  });

  const sendMessage = useMutation({
    mutationFn: (data: ChatRequest) => chatApi.sendMessage(data),
    onSuccess: (response) => {
      store.setIsStreaming(false);
      store.addMessage(response.message);
      if (response.citations?.length) {
        const lastMsg = store.messages[store.messages.length - 1];
        if (lastMsg) {
          store.addMessage({
            ...lastMsg,
            metadata: { citations: response.citations },
          });
        }
      }
    },
    onError: (error: Error) => {
      store.setError(error.message);
      store.setIsStreaming(false);
    },
  });

  const deleteConversation = useMutation({
    mutationFn: (convId: string) => chatApi.deleteConversation(convId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      store.clearChat();
    },
  });

  const getConversation = useCallback(
    async (convId: string) => {
      store.setIsLoading(true);
      try {
        const conv = await chatApi.getConversation(convId);
        store.setCurrentConversation(conv);
      } catch (error) {
        store.setError(error instanceof Error ? error.message : "Failed to load conversation");
      } finally {
        store.setIsLoading(false);
      }
    },
    [store]
  );

  const startNewChat = useCallback(() => {
    store.clearChat();
  }, [store]);

  return {
    conversations: conversationsData?.items ?? [],
    currentConversation: store.currentConversation,
    messages: store.messages,
    isLoading: store.isLoading || isLoadingConversations,
    isStreaming: store.isStreaming,
    error: store.error,
    searchQuery: store.searchQuery,
    setSearchQuery: store.setSearchQuery,
    sendMessage,
    createConversation,
    deleteConversation,
    getConversation,
    startNewChat,
    setIsStreaming: store.setIsStreaming,
  };
}
