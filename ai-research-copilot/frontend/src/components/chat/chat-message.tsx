"use client";

import * as React from "react";
import { Copy, Check, RefreshCw, ThumbsUp, ThumbsDown, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn, copyToClipboard, getInitials } from "@/utils/helpers";

interface ChatMessageProps {
  role: "user" | "assistant" | "system";
  content: string;
  isLoading?: boolean;
  onRegenerate?: () => void;
}

export function ChatMessage({
  role,
  content,
  isLoading,
  onRegenerate,
}: ChatMessageProps) {
  const [copied, setCopied] = React.useState(false);
  const [feedback, setFeedback] = React.useState<"up" | "down" | null>(null);

  const handleCopy = async () => {
    await copyToClipboard(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (role === "system") return null;

  return (
    <div
      className={cn(
        "group flex gap-3 px-4 py-6",
        role === "assistant" && "bg-muted/30"
      )}
    >
      <Avatar className="h-8 w-8 shrink-0">
        <AvatarFallback
          className={cn(
            role === "assistant"
              ? "bg-primary text-primary-foreground"
              : "bg-muted"
          )}
        >
          {role === "assistant" ? (
            <Bot className="h-4 w-4" />
          ) : (
            <User className="h-4 w-4" />
          )}
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-2">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">
            {role === "assistant" ? "AI Assistant" : "You"}
          </span>
        </div>

        <div className="prose prose-sm dark:prose-invert max-w-none">
          {isLoading ? (
            <div className="flex items-center gap-1">
              <div className="h-2 w-2 rounded-full bg-muted-foreground animate-typing-dot" />
              <div className="h-2 w-2 rounded-full bg-muted-foreground animate-typing-dot [animation-delay:0.2s]" />
              <div className="h-2 w-2 rounded-full bg-muted-foreground animate-typing-dot [animation-delay:0.4s]" />
            </div>
          ) : (
            <ReactMarkdown
              components={{
                pre: ({ children }) => (
                  <pre className="overflow-x-auto rounded-lg bg-muted p-4">
                    {children}
                  </pre>
                ),
                code: ({ className, children, ...props }) => {
                  const match = /language-(\w+)/.exec(className || "");
                  if (match) {
                    return (
                      <div className="relative">
                        <div className="absolute right-2 top-2">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                            onClick={() =>
                              copyToClipboard(String(children).replace(/\n$/, ""))
                            }
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                        <code className={className} {...props}>
                          {children}
                        </code>
                      </div>
                    );
                  }
                  return (
                    <code
                      className="rounded bg-muted px-1.5 py-0.5 text-sm"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
              }}
            >
              {content}
            </ReactMarkdown>
          )}
        </div>

        {role === "assistant" && !isLoading && (
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={handleCopy}
            >
              {copied ? (
                <Check className="h-3.5 w-3.5 text-emerald-500" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>
            {onRegenerate && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={onRegenerate}
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-7 w-7",
                feedback === "up" && "text-emerald-500"
              )}
              onClick={() => setFeedback(feedback === "up" ? null : "up")}
            >
              <ThumbsUp className="h-3.5 w-3.5" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className={cn(
                "h-7 w-7",
                feedback === "down" && "text-destructive"
              )}
              onClick={() =>
                setFeedback(feedback === "down" ? null : "down")
              }
            >
              <ThumbsDown className="h-3.5 w-3.5" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
