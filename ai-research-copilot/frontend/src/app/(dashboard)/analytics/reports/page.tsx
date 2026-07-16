"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileBarChart,
  Plus,
  Trash2,
  Download,
  Eye,
  Clock,
  Loader2,
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
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { analyticsApi } from "@/services/api/analytics";
import type { AnalyticsReport } from "@/types/analytics";

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = React.useState(false);

  const { data: reportsData, isLoading } = useQuery({
    queryKey: ["analytics-reports"],
    queryFn: () => analyticsApi.listReports(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => analyticsApi.deleteReport(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["analytics-reports"] }),
  });

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  const reportList: AnalyticsReport[] = reportsData?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Reports</h1>
          <p className="text-muted-foreground">Create and manage analytics reports</p>
        </div>
        <Button onClick={() => setShowCreate(!showCreate)}>
          <Plus className="mr-2 h-4 w-4" /> New Report
        </Button>
      </div>

      {showCreate && (
        <Card>
          <CardHeader><CardTitle>Create Report</CardTitle></CardHeader>
          <CardContent>
            <p className="text-muted-foreground">Use the Analytics page to generate custom reports.</p>
          </CardContent>
        </Card>
      )}

      {reportList.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12">
            <FileBarChart className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">No reports yet</p>
            <p className="text-sm text-muted-foreground">Create your first analytics report to get started.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {reportList.map((report) => (
            <Card key={report.id}>
              <CardContent className="flex items-center justify-between py-4">
                <div className="flex items-center gap-4">
                  <FileBarChart className="h-8 w-8 text-primary" />
                  <div>
                    <p className="font-medium">{report.name}</p>
                    <p className="text-sm text-muted-foreground">{report.description}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Clock className="h-3 w-3 text-muted-foreground" />
                      <span className="text-xs text-muted-foreground">
                        {new Date(report.created_at).toLocaleDateString()}
                      </span>
                      <Badge variant={report.report_type === "scheduled" ? "secondary" : "outline"}>
                        {report.report_type}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon"><Eye className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon"><Download className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="icon" onClick={() => deleteMutation.mutate(report.id)}>
                    {deleteMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
