"use client";

import { Zap, Clock, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/utils/helpers";
import type { AgentExecuteResponse } from "@/types";

interface AgentStatusProps {
  status: AgentExecuteResponse["status"];
  className?: string;
  showLabel?: boolean;
}

const statusConfig = {
  pending: {
    label: "Pending",
    variant: "secondary" as const,
    icon: Clock,
    color: "text-muted-foreground",
  },
  running: {
    label: "Running",
    variant: "info" as const,
    icon: Loader2,
    color: "text-blue-500",
  },
  completed: {
    label: "Completed",
    variant: "success" as const,
    icon: CheckCircle2,
    color: "text-emerald-500",
  },
  failed: {
    label: "Failed",
    variant: "destructive" as const,
    icon: AlertCircle,
    color: "text-destructive",
  },
};

export function AgentStatus({
  status,
  className,
  showLabel = true,
}: AgentStatusProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={cn("gap-1", className)}>
      <Icon
        className={cn(
          "h-3 w-3",
          status === "running" && "animate-spin"
        )}
      />
      {showLabel && config.label}
    </Badge>
  );
}
