"use client";

import * as React from "react";
import { Bot, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import type { Message } from "@/types";

const suggestions = [
  "Explain quantum computing in simple terms",
  "Compare transformer and RNN architectures",
  "What are the latest breakthroughs in AI?",
  "Help me analyze this research paper",
];

interface ChatWindowProps {
  messages: Message[];
  onSend: (message: string) => void;
  isLoading?: boolean;
  conversationId?: string;
}

export function ChatWindow({
  messages,
  onSend,
  isLoading,
  conversationId,
}: ChatWindowProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  React.useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center p-8">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-primary/10 mb-6">
          <Bot className="h-8 w-8 text-primary" />
        </div>
        <h2 className="text-2xl font-bold mb-2">How can I help you today?</h2>
        <p className="text-muted-foreground mb-8 text-center max-w-md">
          I can help with research, analysis, document review, and much more.
          Ask me anything!
        </p>
        <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-2">
          {suggestions.map((suggestion) => (
            <Button
              key={suggestion}
              variant="outline"
              className="justify-start h-auto p-4 text-left"
              onClick={() => onSend(suggestion)}
              disabled={isLoading}
            >
              <Sparkles className="mr-2 h-4 w-4 shrink-0 text-primary" />
              <span className="text-sm">{suggestion}</span>
            </Button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col">
      <div className="flex-1 overflow-auto">
        <div className="mx-auto max-w-3xl">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              role={message.role as "user" | "assistant"}
              content={message.content}
            />
          ))}
          {isLoading && (
            <ChatMessage role="assistant" content="" isLoading />
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>
      <ChatInput onSend={onSend} isLoading={isLoading} />
    </div>
  );
}
