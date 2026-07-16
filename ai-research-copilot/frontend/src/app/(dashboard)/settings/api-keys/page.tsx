"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertTriangle,
  Key,
  Plus,
  Copy,
  Trash2,
  Clock,
} from "lucide-react";
import { toast } from "sonner";
import { formatRelativeTime } from "@/utils/helpers";

export default function ApiKeysSettingsPage() {
  const [keys, setKeys] = React.useState<Array<{ id: string; name: string; prefix: string; created_at: string; last_used_at: string | null; is_active: boolean }>>([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    const loadKeys = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const { usersApi } = await import("@/services/api/users");
        const me = await usersApi.getMe();
        const stored = localStorage.getItem("api_keys");
        const parsed = stored ? JSON.parse(stored) : [];
        setKeys(parsed);
      } catch {
        setError("Failed to load API keys.");
      } finally {
        setIsLoading(false);
      }
    };
    loadKeys();
  }, []);

  const handleCreate = () => {
    const newKey = {
      id: crypto.randomUUID(),
      name: `Key ${keys.length + 1}`,
      prefix: `arc_${Math.random().toString(36).slice(2, 8)}`,
      created_at: new Date().toISOString(),
      last_used_at: null,
      is_active: true,
    };
    const updated = [...keys, newKey];
    setKeys(updated);
    localStorage.setItem("api_keys", JSON.stringify(updated));
    toast.success("API key created. Copy it now - you won't see it again!");
  };

  const handleDelete = (id: string) => {
    const updated = keys.filter((k) => k.id !== id);
    setKeys(updated);
    localStorage.setItem("api_keys", JSON.stringify(updated));
    toast.success("API key deleted.");
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div><Skeleton className="h-8 w-32" /><Skeleton className="h-4 w-48 mt-2" /></div>
          <Skeleton className="h-10 w-36" />
        </div>
        <Card>
          <CardHeader><Skeleton className="h-5 w-24" /><Skeleton className="h-4 w-48 mt-1" /></CardHeader>
          <CardContent>
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full mb-2" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">API Keys</h1>
          <p className="text-muted-foreground">Manage API keys for programmatic access</p>
        </div>
        <Button onClick={handleCreate}><Plus className="mr-2 h-4 w-4" /> Create Key</Button>
      </div>
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Key className="h-5 w-5" />
            Your API Keys
          </CardTitle>
          <CardDescription>
            Keys are used to authenticate API requests. Keep them secure.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {keys.length === 0 ? (
            <div className="flex flex-col items-center py-8 text-center">
              <Key className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-lg font-medium">No API keys yet</p>
              <p className="text-sm text-muted-foreground max-w-sm">
                Create an API key to integrate with external tools and automate workflows.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Key</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Last Used</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {keys.map((key) => (
                  <TableRow key={key.id}>
                    <TableCell className="font-medium">{key.name}</TableCell>
                    <TableCell>
                      <code className="text-xs bg-muted px-2 py-1 rounded">
                        {key.prefix}...
                      </code>
                    </TableCell>
                    <TableCell>
                      <Badge variant={key.is_active ? "success" : "secondary"}>
                        {key.is_active ? "Active" : "Inactive"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatRelativeTime(key.created_at)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {key.last_used_at ? formatRelativeTime(key.last_used_at) : <span className="flex items-center gap-1"><Clock className="h-3 w-3" /> Never</span>}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button variant="ghost" size="icon" onClick={() => { navigator.clipboard.writeText(`${key.prefix}_${key.id}`); toast.success("Copied!"); }}>
                          <Copy className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" onClick={() => handleDelete(key.id)}>
                          <Trash2 className="h-4 w-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
