"use client";

import * as React from "react";
import { useQuery } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Users, Plus, AlertTriangle, Mail, Clock } from "lucide-react";
import { toast } from "sonner";
import { usersApi } from "@/services/api/users";
import { formatRelativeTime } from "@/utils/helpers";

export default function TeamsSettingsPage() {
  const { data: user, isLoading, error } = useQuery({
    queryKey: ["current-user"],
    queryFn: usersApi.getMe,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div><Skeleton className="h-8 w-32" /><Skeleton className="h-4 w-48 mt-2" /></div>
          <Skeleton className="h-10 w-36" />
        </div>
        <Card>
          <CardContent className="flex flex-col items-center py-12">
            <Skeleton className="h-12 w-12 rounded-full mb-4" />
            <Skeleton className="h-5 w-32 mb-2" />
            <Skeleton className="h-4 w-64" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Teams</h1>
          <p className="text-muted-foreground">Manage your teams and collaborators</p>
        </div>
        <Button onClick={() => toast.info("Team creation coming soon!")}>
          <Plus className="mr-2 h-4 w-4" /> Create Team
        </Button>
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>Failed to load team data.</AlertDescription>
        </Alert>
      )}
      <Card>
        <CardContent className="flex flex-col items-center py-12">
          <Users className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-lg font-medium">No teams yet</p>
          <p className="text-sm text-muted-foreground text-center max-w-sm">
            Create a team to collaborate with others on research projects. You can invite team members to share documents, knowledge bases, and workflows.
          </p>
          {user && (
            <div className="mt-6 flex items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1"><Mail className="h-3 w-3" /> {user.email}</span>
              {user.created_at && (
                <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> Joined {formatRelativeTime(user.created_at)}</span>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
