"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  TrendingUp,
  MessageSquare,
  FileText,
  BookOpen,
  Bot,
  Clock,
  ArrowUpRight,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
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
  const { data: summary, isLoading: isLoadingSummary } = useQuery({
    queryKey: ["analytics-summary"],
    queryFn: analyticsApi.getSummary,
  });

  const { data: activityData, isLoading: isLoadingActivity } = useQuery({
    queryKey: ["user-activity"],
    queryFn: () => analyticsApi.getUserActivity(1, 20),
  });

  const { data: visualizations } = useQuery({
    queryKey: ["visualizations"],
    queryFn: () => analyticsApi.listVisualizations(),
  });

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
      icon: Bot,
    },
  ];

  const chartData = [
    { name: "Mon", messages: 45, documents: 12 },
    { name: "Tue", messages: 62, documents: 18 },
    { name: "Wed", messages: 38, documents: 8 },
    { name: "Thu", messages: 73, documents: 22 },
    { name: "Fri", messages: 55, documents: 15 },
    { name: "Sat", messages: 28, documents: 5 },
    { name: "Sun", messages: 15, documents: 3 },
  ];

  const usageData = [
    { name: "GPT-4o", value: 234567 },
    { name: "Claude 3.5 Sonnet", value: 123456 },
    { name: "GPT-3.5 Turbo", value: 567890 },
    { name: "Embeddings", value: 890123 },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground">
            Track usage and monitor your platform activity
          </p>
        </div>
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
          <TabsTrigger value="usage">Token Usage</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <ChartCard
              title="Usage Trends"
              description="Daily messages and documents this week"
              type="bar"
              data={chartData}
              xKey="name"
              yKeys={["messages", "documents"]}
              height={300}
            />

            <ChartCard
              title="Model Distribution"
              description="Token usage by AI model"
              type="pie"
              data={usageData}
              xKey="name"
              yKeys={["value"]}
              height={300}
            />
          </div>

          <ChartCard
            title="Message Activity"
            description="Messages over time"
            type="area"
            data={chartData}
            xKey="name"
            yKeys={["messages"]}
            height={200}
          />
        </TabsContent>

        <TabsContent value="usage" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Token Usage Details</CardTitle>
              <CardDescription>
                Detailed breakdown of token consumption
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {usageData.map((item) => (
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
                            width: `${(item.value / 890123) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
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
              {isLoadingActivity ? (
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
                    {activityData?.items?.length === 0 && (
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
