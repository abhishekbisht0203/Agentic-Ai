"use client";

import * as React from "react";
import {
  MessageSquare,
  FileText,
  Database,
  Bot,
  HardDrive,
  Infinity,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/utils/helpers";
import type { UsageMetric } from "@/types/billing";

const METRIC_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  ai_messages: MessageSquare,
  documents: FileText,
  knowledge_bases: Database,
  agents: Bot,
  storage_bytes: HardDrive,
};

function formatUsageValue(metric: string, value: number): string {
  if (metric === "storage_bytes") {
    if (value >= 1024 * 1024 * 1024) {
      return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`;
    }
    if (value >= 1024 * 1024) {
      return `${(value / (1024 * 1024)).toFixed(1)} MB`;
    }
    if (value >= 1024) {
      return `${(value / 1024).toFixed(1)} KB`;
    }
    return `${value} B`;
  }
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toLocaleString();
}

interface UsageDisplayProps {
  usage: UsageMetric[];
}

export function UsageDisplay({ usage }: UsageDisplayProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage This Month</CardTitle>
        <CardDescription>Track your resource consumption</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-6 md:grid-cols-2">
          {usage.map((item) => {
            const Icon = METRIC_ICONS[item.metric] || MessageSquare;
            const isUnlimited = item.limit === -1;
            const percentage = isUnlimited ? 0 : item.percentage;

            return (
              <div key={item.metric} className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Icon className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">{item.label}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">
                    {isUnlimited ? (
                      <span className="flex items-center gap-1">
                        {formatUsageValue(item.metric, item.used)} /{" "}
                        <Infinity className="h-3 w-3" />
                      </span>
                    ) : (
                      `${formatUsageValue(item.metric, item.used)} / ${formatUsageValue(item.metric, item.limit)}`
                    )}
                  </span>
                </div>
                <Progress
                  value={percentage}
                  className={cn(
                    "h-2",
                    percentage > 80 && "text-destructive",
                    percentage > 60 && percentage <= 80 && "text-amber-500"
                  )}
                />
                {percentage > 80 && !isUnlimited && (
                  <p className="text-xs text-destructive">
                    {Math.round(100 - percentage)}% remaining
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
