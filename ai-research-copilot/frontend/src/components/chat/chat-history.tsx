"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Search,
  MessageSquare,
  Clock,
  Trash2,
  MoreHorizontal,
  PanelLeftClose,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { chatApi } from "@/services/api/chat";
import { useChatStore } from "@/store/chat-store";
import { formatRelativeTime, cn } from "@/utils/helpers";
import { toast } from "sonner";

interface ChatHistoryProps {
  onToggle?: () => void;
}

export function ChatHistory({ onToggle }: ChatHistoryProps) {
  const pathname = usePathname();
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = React.useState("");
  const { currentConversation } = useChatStore();

  const { data: conversationsData, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => chatApi.listConversations(1, 100),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => chatApi.deleteConversation(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      toast.success("Conversation deleted");
    },
    onError: () => {
      toast.error("Failed to delete conversation");
    },
  });

  const conversations = conversationsData?.items ?? [];

  const filteredConversations = conversations.filter((conv) =>
    conv.title?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const recentConversations = filteredConversations;

  return (
    <div className="flex h-full w-72 shrink-0 flex-col border-r bg-background">
      <div className="flex items-center gap-2 p-3">
        <Button asChild className="flex-1 justify-start gap-2" variant="outline">
          <Link href="/chat">
            <Plus className="h-4 w-4" />
            New Chat
          </Link>
        </Button>
        {onToggle && (
          <Button
            variant="outline"
            size="icon"
            className="h-9 w-9 shrink-0"
            onClick={onToggle}
            title="Hide sidebar"
          >
            <PanelLeftClose className="h-4 w-4" />
          </Button>
        )}
      </div>

      <div className="px-3 pb-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            className="pl-9 h-9 text-sm"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <ScrollArea className="flex-1 px-3">
        {isLoading ? (
          <div className="space-y-2 py-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-2 rounded-lg px-2 py-2">
                <div className="h-4 w-4 rounded bg-muted animate-pulse" />
                <div className="flex-1 space-y-1">
                  <div className="h-3 w-full bg-muted animate-pulse rounded" />
                  <div className="h-2 w-16 bg-muted animate-pulse rounded" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div>
            <div className="flex items-center gap-1.5 px-2 py-1.5">
              <Clock className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium text-muted-foreground">
                Recent
              </span>
            </div>
            {recentConversations.map((conv) => (
              <ConversationItem
                key={conv.id}
                conversation={conv}
                isActive={currentConversation?.id === conv.id}
                onDelete={() => deleteMutation.mutate(conv.id)}
              />
            ))}
            {recentConversations.length === 0 && (
              <p className="text-xs text-muted-foreground text-center py-4">
                No conversations yet
              </p>
            )}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

function ConversationItem({
  conversation,
  isActive,
  onDelete,
}: {
  conversation: { id: string; title: string; updated_at: string };
  isActive: boolean;
  onDelete: () => void;
}) {
  const [isHovered, setIsHovered] = React.useState(false);

  return (
    <Link
      href={`/chat?c=${conversation.id}`}
      className={cn(
        "group flex items-center gap-2 rounded-lg px-2 py-2 text-sm cursor-pointer hover:bg-accent transition-colors",
        isActive && "bg-accent"
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
      <div className="flex-1 min-w-0 overflow-hidden">
        <p className="text-sm leading-tight break-words line-clamp-2">{conversation.title || "Untitled"}</p>
        <p className="text-xs text-muted-foreground mt-0.5">
          {formatRelativeTime(conversation.updated_at)}
        </p>
      </div>
      {isHovered && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6 shrink-0"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
              }}
            >
              <MoreHorizontal className="h-3 w-3" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            <DropdownMenuSeparator />
            <DropdownMenuItem
              className="text-destructive"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onDelete();
              }}
            >
              <Trash2 className="mr-2 h-3 w-3" />
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </Link>
  );
}
