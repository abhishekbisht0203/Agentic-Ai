"use client";

import {
  Brain,
  Play,
  Pause,
  MoreHorizontal,
  Trash2,
  Settings,
  Zap,
  Clock,
  CheckCircle2,
  AlertCircle,
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
import { Switch } from "@/components/ui/switch";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { formatRelativeTime } from "@/utils/helpers";
import type { AgentConfiguration } from "@/types";

const statusConfig = {
  idle: { label: "Idle", variant: "secondary" as const, icon: Clock },
  running: { label: "Running", variant: "info" as const, icon: Zap },
  completed: {
    label: "Completed",
    variant: "success" as const,
    icon: CheckCircle2,
  },
  failed: {
    label: "Failed",
    variant: "destructive" as const,
    icon: AlertCircle,
  },
};

const agentTypeColors: Record<string, string> = {
  research: "bg-blue-500/10 text-blue-500",
  analysis: "bg-emerald-500/10 text-emerald-500",
  writing: "bg-violet-500/10 text-violet-500",
  coding: "bg-amber-500/10 text-amber-500",
  supervisor: "bg-pink-500/10 text-pink-500",
  planner: "bg-cyan-500/10 text-cyan-500",
  critic: "bg-red-500/10 text-red-500",
  reviewer: "bg-orange-500/10 text-orange-500",
  memory: "bg-indigo-500/10 text-indigo-500",
  automation: "bg-teal-500/10 text-teal-500",
  document_qa: "bg-lime-500/10 text-lime-500",
  data_analyst: "bg-fuchsia-500/10 text-fuchsia-500",
  code_assistant: "bg-yellow-500/10 text-yellow-500",
  visualization: "bg-purple-500/10 text-purple-500",
  custom: "bg-gray-500/10 text-gray-500",
};

interface AgentCardProps {
  agent: AgentConfiguration;
  status?: keyof typeof statusConfig;
  executionCount?: number;
  lastExecutedAt?: string | null;
  onConfigure?: (agent: AgentConfiguration) => void;
  onExecute?: (agent: AgentConfiguration) => void;
  onDelete?: (agent: AgentConfiguration) => void;
  onToggle?: (agent: AgentConfiguration, active: boolean) => void;
}

export function AgentCard({
  agent,
  status = "idle",
  executionCount = 0,
  lastExecutedAt,
  onConfigure,
  onExecute,
  onDelete,
  onToggle,
}: AgentCardProps) {
  const statusInfo = statusConfig[status];
  const StatusIcon = statusInfo.icon;

  return (
    <Card className="hover:shadow-md transition-all">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div
              className={`flex h-10 w-10 items-center justify-center rounded-lg ${
                agentTypeColors[agent.agent_type] || agentTypeColors.custom
              }`}
            >
              <Brain className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-lg">{agent.name}</CardTitle>
              <CardDescription className="line-clamp-1">
                {agent.description || `${agent.agent_type} agent`}
              </CardDescription>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onConfigure?.(agent)}>
                <Settings className="mr-2 h-4 w-4" />
                Configure
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onExecute?.(agent)}>
                <Play className="mr-2 h-4 w-4" />
                Execute
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive"
                onClick={() => onDelete?.(agent)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Badge variant={statusInfo.variant}>
                <StatusIcon className="mr-1 h-3 w-3" />
                {statusInfo.label}
              </Badge>
              <Badge variant="outline">{agent.model}</Badge>
            </div>
            <Switch
              checked={agent.is_active}
              onCheckedChange={(checked) => onToggle?.(agent, checked)}
            />
          </div>

          <div className="flex items-center justify-between text-sm">
            <span className="text-muted-foreground">
              {executionCount} executions
            </span>
            <span className="text-muted-foreground">
              Last: {lastExecutedAt ? formatRelativeTime(lastExecutedAt) : "Never"}
            </span>
          </div>

          <Button
            className="w-full"
            variant="outline"
            onClick={() => onExecute?.(agent)}
            disabled={status === "running"}
          >
            {status === "running" ? (
              <>
                <Pause className="mr-2 h-4 w-4" />
                Running...
              </>
            ) : (
              <>
                <Play className="mr-2 h-4 w-4" />
                Run Agent
              </>
            )}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
