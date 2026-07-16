"use client";

import * as React from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Bot,
  Clock,
  MessageSquare,
  Zap,
  DollarSign,
  CheckCircle,
  XCircle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle } from "lucide-react";
import { agentPlatformApi } from "@/services/api/agent-platform";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const agentId = params.id as string;

  const { data: agent, isLoading, error } = useQuery({
    queryKey: ["agent-platform", agentId],
    queryFn: () => agentPlatformApi.getAgent(agentId),
    enabled: !!agentId,
  });

  const { data: runs } = useQuery({
    queryKey: ["agent-runs", agentId],
    queryFn: () => agentPlatformApi.getAgentRuns(agentId, { page_size: 10 }),
    enabled: !!agentId,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2">
            <Skeleton className="h-64 w-full" />
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (error || !agent) {
    return (
      <div className="space-y-6">
        <Button variant="ghost" onClick={() => router.push("/agents")}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back to Agents
        </Button>
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>Agent not found.</AlertDescription>
        </Alert>
      </div>
    );
  }

  const stats = [
    { label: "Total Runs", value: agent.total_runs, icon: MessageSquare, color: "text-blue-500" },
    { label: "Avg Latency", value: `${agent.avg_latency_ms}ms`, icon: Clock, color: "text-violet-500" },
    { label: "Success Rate", value: `${agent.success_rate}%`, icon: CheckCircle, color: "text-emerald-500" },
    { label: "Total Tokens", value: agent.total_tokens.toLocaleString(), icon: Zap, color: "text-amber-500" },
    { label: "Total Cost", value: `$${agent.total_cost.toFixed(4)}`, icon: DollarSign, color: "text-emerald-500" },
    { label: "Active Conversations", value: agent.active_conversations, icon: MessageSquare, color: "text-blue-500" },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" onClick={() => router.push("/agents")}>
          <ArrowLeft className="mr-2 h-4 w-4" /> Back
        </Button>
      </div>

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div
            className="flex h-14 w-14 items-center justify-center rounded-xl"
            style={{ backgroundColor: agent.color + "20" }}
          >
            <Bot className="h-7 w-7" style={{ color: agent.color }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold">{agent.name}</h1>
            <p className="text-muted-foreground">{agent.description || "No description"}</p>
          </div>
          <Badge variant={agent.status === "active" ? "success" : "secondary"}>
            {agent.status}
          </Badge>
        </div>
        <Button asChild>
          <Link href={`/agents/${agentId}/chat`}>
            <MessageSquare className="mr-2 h-4 w-4" /> Open Chat
          </Link>
        </Button>
      </div>

      <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">{s.label}</CardTitle>
              <s.icon className={`h-4 w-4 ${s.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-xl font-bold">{s.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Agent settings</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between"><span className="text-sm text-muted-foreground">Model</span><span className="text-sm font-medium">{agent.model}</span></div>
            <div className="flex justify-between"><span className="text-sm text-muted-foreground">Provider</span><span className="text-sm font-medium capitalize">{agent.provider}</span></div>
            <div className="flex justify-between"><span className="text-sm text-muted-foreground">Temperature</span><span className="text-sm font-medium">{agent.temperature}</span></div>
            <div className="flex justify-between"><span className="text-sm text-muted-foreground">Max Tokens</span><span className="text-sm font-medium">{agent.max_tokens}</span></div>
            <div className="flex justify-between"><span className="text-sm text-muted-foreground">Memory</span><Badge variant={agent.memory_enabled ? "success" : "secondary"}>{agent.memory_enabled ? "Enabled" : "Disabled"}</Badge></div>
            <div className="flex justify-between"><span className="text-sm text-muted-foreground">RAG</span><Badge variant={agent.rag_enabled ? "success" : "secondary"}>{agent.rag_enabled ? "Enabled" : "Disabled"}</Badge></div>
            {agent.tools_enabled && agent.tools_enabled.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {agent.tools_enabled.map((t) => (
                  <Badge key={t} variant="outline" className="text-xs">{t}</Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Runs</CardTitle>
            <CardDescription>Last {Math.min(runs?.total ?? 0, 10)} executions</CardDescription>
          </CardHeader>
          <CardContent>
            {!runs?.items?.length ? (
              <p className="text-sm text-muted-foreground text-center py-4">No runs yet</p>
            ) : (
              <div className="space-y-3">
                {runs.items.slice(0, 10).map((run) => (
                  <div key={run.id} className="flex items-center justify-between p-2 border rounded-lg">
                    <div className="flex items-center gap-2">
                      {run.success ? (
                        <CheckCircle className="h-4 w-4 text-emerald-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-red-500" />
                      )}
                      <div>
                        <p className="text-sm font-medium truncate max-w-[200px]">
                          {run.input_text?.slice(0, 60) || "No input"}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {run.latency_ms}ms · {run.tokens_total} tokens
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
