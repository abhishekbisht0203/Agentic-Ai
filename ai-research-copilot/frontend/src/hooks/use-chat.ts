"use client";

import { useCallback, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useChatStore } from "@/store/chat-store";
import { chatApi } from "@/services/api/chat";
import type { ChatRequest, Message } from "@/types";

export function useChat() {
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);

  const conversations = useChatStore((s) => s.conversations);
  const currentConversation = useChatStore((s) => s.currentConversation);
  const messages = useChatStore((s) => s.messages);
  const isLoading = useChatStore((s) => s.isLoading);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const error = useChatStore((s) => s.error);
  const searchQuery = useChatStore((s) => s.searchQuery);

  const setConversations = useChatStore((s) => s.setConversations);
  const setCurrentConversation = useChatStore((s) => s.setCurrentConversation);
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
      const state = useChatStore.getState();
      const msgs = [...state.messages, response.message];
      useChatStore.setState({ messages: msgs });
    },
    onError: (error: Error) => {
      setError(error.message);
      setIsStreaming(false);
    },
  });

  const sendMessageStream = useCallback(
    async (data: ChatRequest) => {
      const convId = data.conversation_id;
      if (!convId) return;

      setError(null);
      setIsStreaming(true);

      const userMsg: Message = {
        id: `user-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`,
        conversation_id: convId,
        role: "user",
        content: data.message,
        metadata: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      const aiMsgId = `ai-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
      const aiMsg: Message = {
        id: aiMsgId,
        conversation_id: convId,
        role: "assistant",
        content: "",
        metadata: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      useChatStore.setState((state) => ({
        messages: [...state.messages, userMsg, aiMsg],
      }));

      let accumulated = "";

      try {
        const stream = chatApi.sendMessageStream(data);
        for await (const event of stream) {
          if (event.error) {
            setError(event.error);
            useChatStore.setState((state) => ({
              messages: state.messages.map((m) =>
                m.id === aiMsgId ? { ...m, content: event.error || "An error occurred." } : m
              ),
            }));
            break;
          }
          if (event.content) {
            accumulated += event.content;
            useChatStore.setState((state) => ({
              messages: state.messages.map((m) =>
                m.id === aiMsgId ? { ...m, content: accumulated } : m
              ),
            }));
          }
          if (event.done) {
            break;
          }
        }
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Stream failed";
        setError(msg);
        useChatStore.setState((state) => ({
          messages: state.messages.map((m) =>
            m.id === aiMsgId ? { ...m, content: msg } : m
          ),
        }));
      } finally {
        setIsStreaming(false);
        queryClient.invalidateQueries({ queryKey: ["conversations"] });
      }
    },
    [setError, setIsStreaming, queryClient]
  );

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
    sendMessageStream,
    createConversation,
    deleteConversation,
    getConversation,
    startNewChat,
    setIsStreaming,
  };
}
