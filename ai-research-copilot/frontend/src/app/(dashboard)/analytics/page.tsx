"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  TrendingUp,
  MessageSquare,
  FileText,
  BookOpen,
  Brain,
  Clock,
  DollarSign,
  Zap,
  AlertTriangle,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ChartCard } from "@/components/analytics/chart-card";
import { analyticsApi } from "@/services/api/analytics";
import { formatRelativeTime, formatBytes } from "@/utils/helpers";

export default function AnalyticsPage() {
  const { data: summary, isLoading: isLoadingSummary, error: summaryError } = useQuery({
    queryKey: ["analytics-summary"],
    queryFn: analyticsApi.getSummary,
  });

  const { data: tokenUsage, isLoading: isLoadingTokens, error: tokenError } = useQuery({
    queryKey: ["token-usage", 30],
    queryFn: () => analyticsApi.getTokenUsage(30),
  });

  const { data: costData, isLoading: isLoadingCosts, error: costError } = useQuery({
    queryKey: ["cost-analytics"],
    queryFn: analyticsApi.getCostAnalytics,
  });

  const { data: modelPerf, isLoading: isLoadingModels, error: modelError } = useQuery({
    queryKey: ["model-performance"],
    queryFn: analyticsApi.getModelPerformance,
  });

  const { data: errorStats, isLoading: isLoadingErrors } = useQuery({
    queryKey: ["error-analytics"],
    queryFn: analyticsApi.getErrorAnalytics,
  });

  const { data: activityData, isLoading: isLoadingActivity, error: activityError } = useQuery({
    queryKey: ["user-activity"],
    queryFn: () => analyticsApi.getUserActivity(1, 20),
  });

  const hasError = summaryError || tokenError || costError || modelError || activityError;

  const stats = [
    {
      title: "Total Messages",
      value: summary?.total_messages ?? 0,
      change: `+${summary?.messages_this_week ?? 0}`,
      icon: MessageSquare,
    },
    {
      title: "Documents Processed",
      value: summary?.total_documents ?? 0,
      change: `+${summary?.documents_this_week ?? 0}`,
      icon: FileText,
    },
    {
      title: "Knowledge Bases",
      value: summary?.total_knowledge_bases ?? 0,
      icon: BookOpen,
    },
    {
      title: "Active Agents",
      value: summary?.active_agents ?? 0,
      icon: Brain,
    },
  ];

  const chartData = tokenUsage?.trend?.map((d) => ({
    name: d.date?.slice(5, 10) || d.date,
    prompt_tokens: d.prompt_tokens,
    completion_tokens: d.completion_tokens,
    requests: d.requests,
  })) ?? [];

  const modelChartData = modelPerf?.models?.map((m) => ({
    name: m.model,
    value: m.total_tokens,
  })) ?? [];

  const costChartData = costData?.breakdown?.map((b) => ({
    name: b.model,
    value: b.cost,
    provider: b.provider,
    requests: b.requests,
    tokens: b.tokens,
  })) ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Track usage, tokens, costs, and platform activity
          </p>
        </div>
      </div>

      {hasError && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Some data failed to load. Please try refreshing the page.
          </AlertDescription>
        </Alert>
      )}

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
                  <Skeleton className="h-3 w-20" />
                </CardContent>
              </Card>
            ))
          : stats.map((stat) => (
              <Card key={stat.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">
                    {stat.title}
                  </CardTitle>
                  <stat.icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {stat.value.toLocaleString()}
                  </div>
                  {stat.change && (
                    <p className="text-xs text-muted-foreground">
                      <span className="text-emerald-500 inline-flex items-center">
                        <TrendingUp className="mr-1 h-3 w-3" />
                        {stat.change}
                      </span>{" "}
                      this week
                    </p>
                  )}
                </CardContent>
              </Card>
            ))}
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="tokens">Token Usage</TabsTrigger>
          <TabsTrigger value="costs">Costs</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Requests</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {isLoadingTokens ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <>
                    <div className="text-2xl font-bold">
                      {(tokenUsage?.summary?.total_requests ?? 0).toLocaleString()}
                    </div>
                    <p className="text-xs text-muted-foreground">Last 30 days</p>
                  </>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
                <Zap className="h-4 w-4 text-amber-500" />
              </CardHeader>
              <CardContent>
                {isLoadingTokens ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <>
                    <div className="text-2xl font-bold">
                      {(tokenUsage?.summary?.total_tokens ?? 0).toLocaleString()}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {(tokenUsage?.summary?.prompt_tokens ?? 0).toLocaleString()} prompt · {(tokenUsage?.summary?.completion_tokens ?? 0).toLocaleString()} completion
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
                <DollarSign className="h-4 w-4 text-emerald-500" />
              </CardHeader>
              <CardContent>
                {isLoadingCosts ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <>
                    <div className="text-2xl font-bold">
                      ${(costData?.total_cost ?? 0).toFixed(4)}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {(costData?.breakdown?.length ?? 0)} provider(s)
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
                <AlertTriangle className="h-4 w-4 text-red-500" />
              </CardHeader>
              <CardContent>
                {isLoadingErrors ? (
                  <Skeleton className="h-8 w-16" />
                ) : (
                  <>
                    <div className="text-2xl font-bold">
                      {errorStats?.error_rate ?? 0}%
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {errorStats?.failed ?? 0} failed of {errorStats?.total ?? 0} requests
                    </p>
                  </>
                )}
              </CardContent>
            </Card>
          </div>

          {chartData.length > 0 && (
            <div className="grid gap-4 lg:grid-cols-2">
              <ChartCard
                title="Token Usage Trend"
                description="Daily prompt and completion tokens (30 days)"
                type="bar"
                data={chartData.slice(-14)}
                xKey="name"
                yKeys={["prompt_tokens", "completion_tokens"]}
                height={300}
              />
              {modelChartData.length > 0 && (
                <ChartCard
                  title="Token Distribution by Model"
                  description="Total tokens used per model"
                  type="pie"
                  data={modelChartData}
                  xKey="name"
                  yKeys={["value"]}
                  height={300}
                />
              )}
            </div>
          )}

          {chartData.length > 0 && (
            <ChartCard
              title="Request Volume"
              description="Daily request count"
              type="area"
              data={chartData.slice(-14)}
              xKey="name"
              yKeys={["requests"]}
              height={200}
            />
          )}
        </TabsContent>

        <TabsContent value="tokens" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Token Usage Details</CardTitle>
              <CardDescription>
                Breakdown of token consumption by model
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingTokens ? (
                <div className="space-y-4">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : modelChartData.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">
                  No token usage data yet. Start using the platform to see metrics.
                </p>
              ) : (
                <div className="space-y-4">
                  {modelChartData.map((item) => {
                    const maxVal = Math.max(...modelChartData.map((d) => d.value));
                    return (
                      <div
                        key={item.name}
                        className="flex items-center justify-between p-4 border rounded-lg"
                      >
                        <div>
                          <p className="font-medium">{item.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {item.value.toLocaleString()} tokens
                          </p>
                        </div>
                        <div className="text-right">
                          <div className="h-2 w-32 rounded-full bg-muted overflow-hidden">
                            <div
                              className="h-full bg-primary rounded-full"
                              style={{
                                width: `${maxVal > 0 ? (item.value / maxVal) * 100 : 0}%`,
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="costs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Cost Breakdown</CardTitle>
              <CardDescription>
                API costs by provider and model
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingCosts ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : costChartData.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">
                  No cost data yet. API usage will appear here.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Provider</TableHead>
                      <TableHead>Model</TableHead>
                      <TableHead className="text-right">Requests</TableHead>
                      <TableHead className="text-right">Tokens</TableHead>
                      <TableHead className="text-right">Cost</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {costChartData.map((item) => (
                      <TableRow key={`${item.provider}-${item.name}`}>
                        <TableCell>
                          <Badge variant="outline" className="capitalize">
                            {item.provider}
                          </Badge>
                        </TableCell>
                        <TableCell className="font-medium">{item.name}</TableCell>
                        <TableCell className="text-right">{item.requests.toLocaleString()}</TableCell>
                        <TableCell className="text-right">{item.tokens.toLocaleString()}</TableCell>
                        <TableCell className="text-right font-medium">
                          ${item.value.toFixed(4)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Model Performance</CardTitle>
              <CardDescription>
                Latency and usage statistics by model
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isLoadingModels ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : !modelPerf?.models?.length ? (
                <p className="text-muted-foreground text-center py-4">
                  No model performance data yet.
                </p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Provider</TableHead>
                      <TableHead>Model</TableHead>
                      <TableHead className="text-right">Requests</TableHead>
                      <TableHead className="text-right">Avg Duration</TableHead>
                      <TableHead className="text-right">Total Tokens</TableHead>
                      <TableHead className="text-right">Cost</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {modelPerf.models.map((m) => (
                      <TableRow key={`${m.provider}-${m.model}`}>
                        <TableCell className="capitalize">{m.provider}</TableCell>
                        <TableCell className="font-medium">{m.model}</TableCell>
                        <TableCell className="text-right">{m.requests.toLocaleString()}</TableCell>
                        <TableCell className="text-right">{m.avg_duration_ms}ms</TableCell>
                        <TableCell className="text-right">{m.total_tokens.toLocaleString()}</TableCell>
                        <TableCell className="text-right">${m.cost.toFixed(4)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>
                Your latest actions on the platform
              </CardDescription>
            </CardHeader>
            <CardContent>
              {activityError ? (
                <p className="text-sm text-destructive text-center py-4">
                  Failed to load activity data.
                </p>
              ) : isLoadingActivity ? (
                <div className="space-y-3">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Action</TableHead>
                      <TableHead>Resource</TableHead>
                      <TableHead>Time</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {activityData?.items?.map((activity) => (
                      <TableRow key={activity.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Clock className="h-4 w-4 text-muted-foreground" />
                            <span className="text-sm">{activity.action}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-muted-foreground">
                            {activity.resource_type}
                            {activity.resource_id &&
                              ` (${activity.resource_id.slice(0, 8)}...)`}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="text-sm text-muted-foreground">
                            {formatRelativeTime(activity.created_at)}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                    {(!activityData?.items || activityData.items.length === 0) && (
                      <TableRow>
                        <TableCell
                          colSpan={3}
                          className="h-24 text-center text-muted-foreground"
                        >
                          No recent activity
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
