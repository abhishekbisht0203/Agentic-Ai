"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { PanelLeft } from "lucide-react";
import { useChat } from "@/hooks/use-chat";
import { ChatHistory } from "@/components/chat/chat-history";
import { ChatWindow } from "@/components/chat/chat-window";
import { toast } from "sonner";
import { documentsApi } from "@/services/api/documents";

export default function ChatPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const conversationId = searchParams.get("c");
  const [sidebarOpen, setSidebarOpen] = React.useState(true);
  const {
    currentConversation,
    messages,
    isLoading,
    isStreaming,
    sendMessageStream,
    createConversation,
    getConversation,
    startNewChat,
    stopStream,
  } = useChat();

  React.useEffect(() => {
    if (conversationId) {
      getConversation(conversationId);
    } else {
      startNewChat();
    }
  }, [conversationId, getConversation, startNewChat]);

  const handleSend = async (content: string, attachments?: File[]) => {
    try {
      let convId = currentConversation?.id;

      if (!convId) {
        const newConv = await createConversation.mutateAsync({
          title: content.slice(0, 100),
        });
        convId = newConv.id;
        router.replace(`/chat?c=${convId}`);
      }

      // Upload any pending attachments with the conversation ID
      if (attachments && attachments.length > 0 && convId) {
        try {
          for (const file of attachments) {
            await documentsApi.uploadDocument(file, file.name, undefined, convId);
          }
          toast.success(`${attachments.length} file(s) attached`);
        } catch (err) {
          toast.error("Failed to attach some files");
        }
      }

      if (convId) {
        await sendMessageStream({
          message: content,
          conversation_id: convId,
        });
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : "Failed to send message";
      toast.error(msg);
    }
  };

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {sidebarOpen && (
        <ChatHistory onToggle={() => setSidebarOpen(false)} />
      )}
      <div className="flex-1 flex flex-col min-w-0">
        {!sidebarOpen && (
          <div className="flex items-center px-3 py-2">
            <button
              onClick={() => setSidebarOpen(true)}
              className="flex items-center justify-center h-9 w-9 rounded-lg border bg-muted hover:bg-accent transition-colors"
              title="Show chat history"
            >
              <PanelLeft className="h-4 w-4" />
            </button>
          </div>
        )}
        <ChatWindow
          messages={messages}
          onSend={handleSend}
          onStop={stopStream}
          isLoading={isLoading || isStreaming}
          conversationId={currentConversation?.id}
        />
      </div>
    </div>
  );
}
