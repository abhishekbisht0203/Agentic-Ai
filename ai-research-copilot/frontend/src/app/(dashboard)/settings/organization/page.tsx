"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { usersApi } from "@/services/api/users";

export default function OrganizationSettingsPage() {
  const queryClient = useQueryClient();
  const [orgName, setOrgName] = React.useState("");

  const { data: user, isLoading, error } = useQuery({
    queryKey: ["current-user"],
    queryFn: usersApi.getMe,
  });

  React.useEffect(() => {
    if (user?.full_name) setOrgName(user.full_name);
  }, [user]);

  const updateMutation = useMutation({
    mutationFn: (name: string) => usersApi.updateMe({ full_name: name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["current-user"] });
      toast.success("Organization settings updated.");
    },
    onError: () => toast.error("Failed to save settings."),
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div><Skeleton className="h-8 w-48" /><Skeleton className="h-4 w-64 mt-2" /></div>
        <Card>
          <CardHeader><Skeleton className="h-5 w-40" /><Skeleton className="h-4 w-56 mt-1" /></CardHeader>
          <CardContent className="space-y-4">
            <Skeleton className="h-10 w-80" />
            <Skeleton className="h-10 w-32" />
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Organization</h1>
        <p className="text-muted-foreground">Manage your organization settings</p>
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>Failed to load organization data.</AlertDescription>
        </Alert>
      )}
      <Card>
        <CardHeader>
          <CardTitle>Organization Details</CardTitle>
          <CardDescription>Update your organization name and profile</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid max-w-sm gap-1.5">
            <Label htmlFor="org-name">Organization Name</Label>
            <Input id="org-name" value={orgName} onChange={(e) => setOrgName(e.target.value)} placeholder="My Organization" />
          </div>
          <Button onClick={() => updateMutation.mutate(orgName)} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? "Saving..." : "Save Changes"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
