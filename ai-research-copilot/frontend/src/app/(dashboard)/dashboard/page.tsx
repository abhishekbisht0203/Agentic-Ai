"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  MessageSquare,
  FileText,
  BookOpen,
  Brain,
  ArrowUpRight,
  ArrowRight,
  TrendingUp,
  Clock,
  Zap,
  Upload,
  GitBranch,
  Loader2,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/store/auth-store";
import { analyticsApi } from "@/services/api/analytics";
import { chatApi } from "@/services/api/chat";
import { documentsApi } from "@/services/api/documents";
import { formatRelativeTime, formatBytes } from "@/utils/helpers";

export default function DashboardPage() {
  const { user } = useAuthStore();

  const { data: summary, isLoading: isLoadingSummary } = useQuery({
    queryKey: ["analytics-summary"],
    queryFn: analyticsApi.getSummary,
  });

  const { data: conversations, isLoading: isLoadingConversations } = useQuery({
    queryKey: ["conversations", { page: 1, page_size: 5 }],
    queryFn: () => chatApi.listConversations(1, 5),
  });

  const { data: documents, isLoading: isLoadingDocuments } = useQuery({
    queryKey: ["documents", { page: 1, page_size: 5 }],
    queryFn: () => documentsApi.listDocuments(1, 5),
  });

  const { data: activity } = useQuery({
    queryKey: ["user-activity"],
    queryFn: () => analyticsApi.getUserActivity(1, 10),
  });

  const stats = [
    {
      title: "Total Conversations",
      value: summary?.total_conversations ?? 0,
      change: summary?.conversations_this_week ?? 0,
      changeLabel: "this week",
      icon: MessageSquare,
      href: "/chat",
    },
    {
      title: "Documents",
      value: summary?.total_documents ?? 0,
      change: summary?.documents_this_week ?? 0,
      changeLabel: "this week",
      icon: FileText,
      href: "/documents",
    },
    {
      title: "Knowledge Bases",
      value: summary?.total_knowledge_bases ?? 0,
      icon: BookOpen,
      href: "/knowledge",
    },
    {
      title: "Active Agents",
      value: summary?.active_agents ?? 0,
      icon: Brain,
      href: "/agents",
    },
  ];

  const quickActions = [
    {
      title: "New Chat",
      description: "Start a conversation with AI",
      icon: MessageSquare,
      href: "/chat",
      color: "text-blue-500",
    },
    {
      title: "Upload Document",
      description: "Add files to your knowledge base",
      icon: Upload,
      href: "/documents",
      color: "text-emerald-500",
    },
    {
      title: "Knowledge Base",
      description: "Organize your documents",
      icon: BookOpen,
      href: "/knowledge",
      color: "text-violet-500",
    },
    {
      title: "Run Agent",
      description: "Execute an AI agent task",
      icon: Brain,
      href: "/agents",
      color: "text-amber-500",
    },
  ];

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">
            Welcome back, {user?.full_name || user?.username || "User"}
          </h1>
          <p className="text-muted-foreground">
            Here&apos;s what&apos;s happening with your research platform.
          </p>
        </div>
        <Button asChild>
          <Link href="/chat">
            New Chat
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {isLoadingSummary
          ? Array.from({ length: 4 }).map((_, i) => (
              <Card key={i}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-4 w-4" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-8 w-16 mb-2" />
                  <Skeleton className="h-3 w-32" />
                </CardContent>
              </Card>
            ))
          : stats.map((stat) => (
              <Link key={stat.title} href={stat.href}>
                <Card className="hover:shadow-md transition-all cursor-pointer">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">
                      {stat.title}
                    </CardTitle>
                    <stat.icon className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stat.value.toLocaleString()}</div>
                    {stat.change !== undefined && (
                      <p className="text-xs text-muted-foreground">
                        <span className="text-emerald-500 inline-flex items-center">
                          <TrendingUp className="mr-1 h-3 w-3" />
                          +{stat.change}
                        </span>{" "}
                        {stat.changeLabel}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </Link>
            ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Jump into your workflow</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3">
              {quickActions.map((action) => (
                <Link key={action.title} href={action.href}>
                  <div className="group rounded-lg border p-4 hover:bg-muted/50 transition-colors cursor-pointer">
                    <action.icon
                      className={`h-5 w-5 ${action.color} mb-2`}
                    />
                    <h3 className="text-sm font-medium group-hover:text-primary transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      {action.description}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Your latest actions</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/analytics">
                  View all
                  <ArrowUpRight className="ml-1 h-3 w-3" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoadingConversations ? (
              <div className="space-y-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <Skeleton className="h-4 w-4 mt-0.5" />
                    <div className="flex-1 space-y-1">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-3 w-20" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-4">
                {conversations?.items?.slice(0, 5).map((conv) => (
                  <Link
                    key={conv.id}
                    href={`/chat?c=${conv.id}`}
                    className="flex items-start gap-3 group"
                  >
                    <div className="mt-0.5">
                      <MessageSquare className="h-4 w-4 text-blue-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                        {conv.title}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <Clock className="h-3 w-3 text-muted-foreground" />
                        <span className="text-xs text-muted-foreground">
                          {conv.last_message_at
                            ? formatRelativeTime(conv.last_message_at)
                            : "No messages"}
                        </span>
                        <Badge
                          variant={conv.status === "active" ? "success" : "secondary"}
                          className="text-[10px] px-1.5 py-0"
                        >
                          {conv.status}
                        </Badge>
                      </div>
                    </div>
                  </Link>
                ))}
                {conversations?.items?.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No conversations yet. Start a new chat!
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Documents</CardTitle>
                <CardDescription>Latest uploaded files</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/documents">
                  View all
                  <ArrowUpRight className="ml-1 h-3 w-3" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoadingDocuments ? (
              <div className="space-y-3">
                {Array.from({ length: 3 }).map((_, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <Skeleton className="h-10 w-10 rounded-lg" />
                    <div className="flex-1 space-y-1">
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-3 w-24" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="space-y-3">
                {documents?.items?.slice(0, 5).map((doc) => (
                  <Link
                    key={doc.id}
                    href={`/documents?view=${doc.id}`}
                    className="flex items-center gap-3 group"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
                      <FileText className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate group-hover:text-primary transition-colors">
                        {doc.name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {formatBytes(doc.file_size)} · {doc.chunk_count} chunks
                      </p>
                    </div>
                    <Badge
                      variant={
                        doc.status === "completed"
                          ? "success"
                          : doc.status === "processing"
                          ? "warning"
                          : "destructive"
                      }
                      className="text-[10px]"
                    >
                      {doc.status}
                    </Badge>
                  </Link>
                ))}
                {documents?.items?.length === 0 && (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No documents uploaded yet.
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Platform Overview</CardTitle>
                <CardDescription>System statistics</CardDescription>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/analytics">
                  Details
                  <ArrowUpRight className="ml-1 h-3 w-3" />
                </Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-blue-500" />
                  <span className="text-sm">Total Messages</span>
                </div>
                <span className="text-sm font-medium">
                  {(summary?.total_messages ?? 0).toLocaleString()}
                </span>
              </div>
              <div className="h-px bg-border" />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-500" />
                  <span className="text-sm">Tokens Used</span>
                </div>
                <span className="text-sm font-medium">
                  {(summary?.total_tokens_used ?? 0).toLocaleString()}
                </span>
              </div>
              <div className="h-px bg-border" />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <GitBranch className="h-4 w-4 text-violet-500" />
                  <span className="text-sm">Active Workflows</span>
                </div>
                <span className="text-sm font-medium">
                  {summary?.active_workflows ?? 0}
                </span>
              </div>
              <div className="h-px bg-border" />
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileText className="h-4 w-4 text-emerald-500" />
                  <span className="text-sm">Storage Used</span>
                </div>
                <span className="text-sm font-medium">
                  {formatBytes(summary?.total_storage_used_bytes ?? 0)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
