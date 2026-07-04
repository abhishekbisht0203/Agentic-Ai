"use client";

import { useCallback, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useChatStore } from "@/store/chat-store";
import { chatApi } from "@/services/api/chat";
import type { ChatRequest } from "@/types";

export function useChat() {
  const queryClient = useQueryClient();

  const conversations = useChatStore((s) => s.conversations);
  const currentConversation = useChatStore((s) => s.currentConversation);
  const messages = useChatStore((s) => s.messages);
  const isLoading = useChatStore((s) => s.isLoading);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const error = useChatStore((s) => s.error);
  const searchQuery = useChatStore((s) => s.searchQuery);

  const setConversations = useChatStore((s) => s.setConversations);
  const setCurrentConversation = useChatStore((s) => s.setCurrentConversation);
  const addMessage = useChatStore((s) => s.addMessage);
  const setIsLoading = useChatStore((s) => s.setIsLoading);
  const setIsStreaming = useChatStore((s) => s.setIsStreaming);
  const setError = useChatStore((s) => s.setError);
  const setSearchQuery = useChatStore((s) => s.setSearchQuery);
  const clearChat = useChatStore((s) => s.clearChat);

  const { data: conversationsData, isLoading: isLoadingConversations } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => chatApi.listConversations(),
  });

  const createConversation = useMutation({
    mutationFn: (data: { title?: string; agent_type?: string; knowledge_base_id?: string }) =>
      chatApi.createConversation(data),
    onSuccess: (newConv) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      setCurrentConversation({ ...newConv, messages: [] });
      return newConv;
    },
  });

  const sendMessage = useMutation({
    mutationFn: (data: ChatRequest) => chatApi.sendMessage(data),
    onSuccess: (response) => {
      setIsStreaming(false);
      addMessage(response.message);
      if (response.citations?.length) {
        const currentMessages = useChatStore.getState().messages;
        const lastMsg = currentMessages[currentMessages.length - 1];
        if (lastMsg) {
          addMessage({
            ...lastMsg,
            metadata: { citations: response.citations },
          });
        }
      }
    },
    onError: (error: Error) => {
      setError(error.message);
      setIsStreaming(false);
    },
  });

  const deleteConversation = useMutation({
    mutationFn: (convId: string) => chatApi.deleteConversation(convId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      clearChat();
    },
  });

  const getConversation = useCallback(
    async (convId: string) => {
      setIsLoading(true);
      try {
        const conv = await chatApi.getConversation(convId);
        setCurrentConversation(conv);
      } catch (error) {
        setError(error instanceof Error ? error.message : "Failed to load conversation");
      } finally {
        setIsLoading(false);
      }
    },
    [setIsLoading, setCurrentConversation, setError]
  );

  const startNewChat = useCallback(() => {
    clearChat();
  }, [clearChat]);

  return {
    conversations: conversationsData?.items ?? [],
    currentConversation,
    messages,
    isLoading: isLoading || isLoadingConversations,
    isStreaming,
    error,
    searchQuery,
    setSearchQuery,
    sendMessage,
    createConversation,
    deleteConversation,
    getConversation,
    startNewChat,
    setIsStreaming,
  };
}
