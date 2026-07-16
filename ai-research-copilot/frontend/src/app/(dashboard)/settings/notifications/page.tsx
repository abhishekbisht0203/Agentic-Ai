"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { settingsApi } from "@/services/api/settings";

export default function NotificationsSettingsPage() {
  const queryClient = useQueryClient();

  const { data: prefs, isLoading, error } = useQuery({
    queryKey: ["settings-preferences"],
    queryFn: settingsApi.getPreferences,
  });

  const [local, setLocal] = React.useState({
    notifications_email: true,
    notifications_tasks: true,
    notifications_documents: true,
    notifications_weekly: true,
  });

  React.useEffect(() => {
    if (prefs) {
      setLocal({
        notifications_email: prefs.notifications_email ?? true,
        notifications_tasks: prefs.notifications_tasks ?? true,
        notifications_documents: prefs.notifications_documents ?? true,
        notifications_weekly: prefs.notifications_weekly ?? true,
      });
    }
  }, [prefs]);

  const updateMutation = useMutation({
    mutationFn: (data: Partial<typeof local>) => settingsApi.updatePreferences(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["settings-preferences"] });
      toast.success("Notification preferences updated.");
    },
    onError: () => toast.error("Failed to save preferences."),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div><Skeleton className="h-8 w-48" /><Skeleton className="h-4 w-64 mt-2" /></div>
        <Card>
          <CardHeader><Skeleton className="h-5 w-40" /><Skeleton className="h-4 w-56 mt-1" /></CardHeader>
          <CardContent className="space-y-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="flex items-center justify-between">
                <div><Skeleton className="h-4 w-32" /><Skeleton className="h-3 w-48 mt-1" /></div>
                <Skeleton className="h-6 w-10 rounded-full" />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Notifications</h1>
        <p className="text-muted-foreground">Configure how you receive notifications</p>
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>Failed to load preferences. Using defaults.</AlertDescription>
        </Alert>
      )}
      <Card>
        <CardHeader>
          <CardTitle>Notification Preferences</CardTitle>
          <CardDescription>Choose which notifications you want to receive</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <Label>Email Notifications</Label>
              <p className="text-sm text-muted-foreground">Receive notifications via email</p>
            </div>
            <Switch checked={local.notifications_email} onCheckedChange={(v) => setLocal({ ...local, notifications_email: v })} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>Task Alerts</Label>
              <p className="text-sm text-muted-foreground">Get notified when tasks are completed</p>
            </div>
            <Switch checked={local.notifications_tasks} onCheckedChange={(v) => setLocal({ ...local, notifications_tasks: v })} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>Document Updates</Label>
              <p className="text-sm text-muted-foreground">When documents are processed or shared</p>
            </div>
            <Switch checked={local.notifications_documents} onCheckedChange={(v) => setLocal({ ...local, notifications_documents: v })} />
          </div>
          <div className="flex items-center justify-between">
            <div>
              <Label>Weekly Digest</Label>
              <p className="text-sm text-muted-foreground">Weekly summary of your research activity</p>
            </div>
            <Switch checked={local.notifications_weekly} onCheckedChange={(v) => setLocal({ ...local, notifications_weekly: v })} />
          </div>
          <Button onClick={() => updateMutation.mutate(local)} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? "Saving..." : "Save Preferences"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
