"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation } from "@tanstack/react-query";
import {
  ArrowLeft,
  Bot,
  Send,
  Loader2,
  AlertTriangle,
  Copy,
  Check,
} from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { toast } from "sonner";
import { agentPlatformApi } from "@/services/api/agent-platform";
import ReactMarkdown from "react-markdown";

interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: Date;
}

export default function AgentChatPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState("");
  const [conversationId, setConversationId] = React.useState<string | null>(null);
  const [isStreaming, setIsStreaming] = React.useState(false);
  const scrollRef = React.useRef<HTMLDivElement>(null);

  const { data: agent, isLoading, error } = useQuery({
    queryKey: ["agent-platform", agentId],
    queryFn: () => agentPlatformApi.getAgent(agentId),
    enabled: !!agentId,
  });

  React.useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const chatMutation = useMutation({
    mutationFn: (message: string) =>
      agentPlatformApi.sendChatMessage(agentId, {
        message,
        conversation_id: conversationId ?? undefined,
      }),
    onSuccess: (data) => {
      setConversationId(data.conversation_id);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: data.message,
          timestamp: new Date(),
        },
      ]);
      setIsStreaming(false);
    },
    onError: (err: Error) => {
      setIsStreaming(false);
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `**Error:** ${err.message || "Failed to get response"}`,
          timestamp: new Date(),
        },
      ]);
    },
  });

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isStreaming) return;
    setInput("");
    setIsStreaming(true);
    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: text, timestamp: new Date() },
    ]);
    chatMutation.mutate(text);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col h-[calc(100vh-4rem)]">
        <div className="flex items-center gap-4 p-4 border-b">
          <Skeleton className="h-8 w-8" />
          <div><Skeleton className="h-5 w-32" /><Skeleton className="h-3 w-48 mt-1" /></div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="p-6">
        <Button variant="ghost" onClick={() => router.push("/agents")}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
        <Alert variant="destructive" className="mt-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>Agent not found or failed to load.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <div className="flex items-center justify-between p-4 border-b bg-background">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => router.push("/agents")}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div
            className="flex h-9 w-9 items-center justify-center rounded-lg"
            style={{ backgroundColor: agent.color + "20" }}
          >
            <Bot className="h-5 w-5" style={{ color: agent.color }} />
          </div>
          <div>
            <p className="font-medium">{agent.name}</p>
            <p className="text-xs text-muted-foreground">{agent.model}</p>
          </div>
          <Badge variant={agent.status === "active" ? "success" : "secondary"} className="ml-2">
            {agent.status}
          </Badge>
        </div>
        <Button variant="outline" size="sm" onClick={() => { setMessages([]); setConversationId(null); }}>
          New Chat
        </Button>
      </div>

      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div
              className="flex h-16 w-16 items-center justify-center rounded-2xl mb-4"
              style={{ backgroundColor: agent.color + "20" }}
            >
              <Bot className="h-8 w-8" style={{ color: agent.color }} />
            </div>
            <h2 className="text-xl font-semibold">Chat with {agent.name}</h2>
            <p className="text-muted-foreground max-w-md mt-2">
              {agent.description || `Send a message to start the conversation.`}
            </p>
          </div>
        ) : (
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      <div className="border-t p-4 bg-background">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className="min-h-[44px] max-h-[120px] resize-none"
            rows={1}
            disabled={isStreaming}
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || isStreaming}
            className="h-[44px]"
          >
            {isStreaming ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: ChatMessage }) {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          message.role === "user"
            ? "bg-primary text-primary-foreground"
            : "bg-muted"
        }`}
      >
        {message.role === "assistant" ? (
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <ReactMarkdown
              components={{
                code: ({ className, children, ...props }) => {
                  const isInline = !className;
                  if (isInline) {
                    return <code className="bg-muted-foreground/20 px-1 py-0.5 rounded text-sm" {...props}>{children}</code>;
                  }
                  return (
                    <div className="relative group">
                      <pre className="bg-muted-foreground/10 rounded-lg p-4 overflow-x-auto">
                        <code className={className} {...props}>{children}</code>
                      </pre>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(String(children).replace(/\n$/, ""));
                          toast.success("Copied to clipboard");
                        }}
                        className="absolute top-2 right-2 p-1 rounded bg-muted-foreground/20 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <Copy className="h-3 w-3" />
                      </button>
                    </div>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        )}
        <div className={`flex items-center gap-2 mt-1 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
          <span className="text-[10px] opacity-70">
            {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
          </span>
          {message.role === "assistant" && (
            <button onClick={handleCopy} className="opacity-50 hover:opacity-100 transition-opacity">
              {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
