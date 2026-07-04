"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useChat } from "@/hooks/use-chat";
import { ChatHistory } from "@/components/chat/chat-history";
import { ChatWindow } from "@/components/chat/chat-window";
import { toast } from "sonner";

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const conversationId = searchParams.get("c");
  const {
    currentConversation,
    messages,
    isLoading,
    isStreaming,
    sendMessage,
    createConversation,
    getConversation,
    startNewChat,
  } = useChat();

  React.useEffect(() => {
    if (conversationId) {
      getConversation(conversationId);
    } else {
      startNewChat();
    }
  }, [conversationId, getConversation, startNewChat]);

  const handleSend = async (content: string) => {
    try {
      let convId = currentConversation?.id;

      if (!convId) {
        const newConv = await createConversation.mutateAsync({
          title: content.slice(0, 100),
        });
        convId = newConv.id;
        router.replace(`/chat?c=${convId}`);
      }

      if (convId) {
        await sendMessage.mutateAsync({
          message: content,
          conversation_id: convId,
        });
      }
    } catch (error) {
      toast.error("Failed to send message");
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)] -m-6">
      <ChatHistory />
      <div className="flex-1 flex flex-col">
        <ChatWindow
          messages={messages}
          onSend={handleSend}
          isLoading={isLoading || isStreaming}
          conversationId={currentConversation?.id}
        />
      </div>
    </div>
  );
}
