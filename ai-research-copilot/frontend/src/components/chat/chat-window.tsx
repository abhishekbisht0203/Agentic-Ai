"use client";

import * as React from "react";
import { Brain, Sparkles, FileText, Code, Lightbulb, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import type { Message } from "@/types";

const suggestions = [
  {
    icon: Search,
    label: "Research any topic",
    message: "Help me research the latest developments in quantum computing",
  },
  {
    icon: FileText,
    label: "Analyze documents",
    message: "I've uploaded a research paper. Can you analyze it and summarize the key findings?",
  },
  {
    icon: Code,
    label: "Generate code",
    message: "Write a Python script to scrape and analyze research papers from arXiv",
  },
  {
    icon: Lightbulb,
    label: "Explain concepts",
    message: "Explain the difference between transformers and RNNs in simple terms",
  },
];

interface ChatWindowProps {
  messages: Message[];
  onSend: (message: string, attachments?: File[]) => void;
  onStop?: () => void;
  isLoading?: boolean;
  conversationId?: string;
}

export function ChatWindow({
  messages,
  onSend,
  onStop,
  isLoading,
  conversationId,
}: ChatWindowProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = React.useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  React.useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const displayMessages = React.useMemo(
    () =>
      messages.filter((msg) => {
        if (msg.role === "user") return true;
        if (msg.status === "failed") return !!msg.content;
        if (msg.status === "streaming" && !msg.content) return false;
        return true;
      }),
    [messages]
  );

  const handleSend = React.useCallback(
    (message: string, attachments?: File[]) => {
      onSend(message, attachments);
    },
    [onSend]
  );

  return (
    <div className="flex flex-1 flex-col min-h-0">
      {displayMessages.length === 0 && !isLoading ? (
        <div className="flex flex-1 flex-col items-center justify-center p-8">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-primary/70 mb-6 shadow-lg shadow-primary/20">
            <Brain className="h-8 w-8 text-primary-foreground" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Welcome back!</h2>
          <p className="text-muted-foreground mb-2 text-center max-w-md">
            I&apos;m <span className="font-semibold text-foreground">ARC</span>, your AI Research Copilot.
          </p>
          <p className="text-muted-foreground mb-8 text-center max-w-md text-sm">
            I can help you research, analyze, and build. Upload documents,
            ask questions, or start exploring.
          </p>
          <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-2">
            {suggestions.map((suggestion) => (
              <Button
                key={suggestion.label}
                variant="outline"
                className="justify-start h-auto p-4 text-left"
                onClick={() => handleSend(suggestion.message)}
                disabled={isLoading}
              >
                <suggestion.icon className="mr-2 h-4 w-4 shrink-0 text-primary" />
                <span className="text-sm">{suggestion.label}</span>
              </Button>
            ))}
          </div>
        </div>
      ) : (
        <div ref={containerRef} className="flex-1 overflow-auto">
          <div className="mx-auto max-w-3xl">
            {displayMessages.map((message, index) => {
              const isLastMessage = index === displayMessages.length - 1;
              const showTypingIndicator =
                isLoading &&
                message.role === "assistant" &&
                message.status === "streaming" &&
                isLastMessage &&
                !message.content;

              return (
                <ChatMessage
                  key={message.id}
                  role={message.role as "user" | "assistant"}
                  content={message.content}
                  isLoading={showTypingIndicator}
                />
              );
            })}
            <div ref={messagesEndRef} />
          </div>
        </div>
      )}
      <ChatInput
        onSend={handleSend}
        onStop={onStop}
        isLoading={isLoading}
        conversationId={conversationId}
      />
    </div>
  );
}
