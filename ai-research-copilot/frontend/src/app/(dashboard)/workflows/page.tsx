"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  GitBranch,
  Plus,
  Play,
  MoreHorizontal,
  Trash2,
  Edit,
  Clock,
  CheckCircle2,
  AlertCircle,
  Pause,
  Loader2,
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
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { workflowsApi } from "@/services/api/workflows";
import { formatRelativeTime } from "@/utils/helpers";
import { toast } from "sonner";
import type { Workflow } from "@/types";

const statusConfig = {
  active: {
    label: "Active",
    variant: "success" as const,
    icon: CheckCircle2,
  },
  draft: { label: "Draft", variant: "secondary" as const, icon: Edit },
  paused: { label: "Paused", variant: "warning" as const, icon: Pause },
  archived: {
    label: "Archived",
    variant: "outline" as const,
    icon: Clock,
  },
};

export default function WorkflowsPage() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setIsCreateOpen] = React.useState(false);
  const [editingWorkflow, setEditingWorkflow] = React.useState<Workflow | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["workflows"],
    queryFn: () => workflowsApi.listWorkflows(),
  });

  const createMutation = useMutation({
    mutationFn: workflowsApi.createWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      setIsCreateOpen(false);
      toast.success("Workflow created");
    },
    onError: () => {
      toast.error("Failed to create workflow");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: workflowsApi.deleteWorkflow,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      toast.success("Workflow deleted");
    },
    onError: () => {
      toast.error("Failed to delete workflow");
    },
  });

  const executeMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: { input_data: Record<string, unknown> } }) =>
      workflowsApi.executeWorkflow(id, data),
    onSuccess: () => {
      toast.success("Workflow execution started");
    },
    onError: () => {
      toast.error("Failed to execute workflow");
    },
  });

  const workflows = data?.items ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Workflows</h1>
          <p className="text-muted-foreground">
            Build and automate research pipelines
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Workflow
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="flex items-center gap-4">
                  <Skeleton className="h-12 w-12 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-5 w-48" />
                    <Skeleton className="h-3 w-full" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : workflows.length === 0 ? (
        <div className="text-center py-12">
          <GitBranch className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
          <p className="text-muted-foreground">
            No workflows yet. Create one to get started.
          </p>
        </div>
      ) : (
        <div className="grid gap-4">
          {workflows.map((workflow) => {
            const status =
              statusConfig[workflow.status as keyof typeof statusConfig];
            const StatusIcon = status?.icon || Clock;
            return (
              <Card key={workflow.id} className="hover:shadow-md transition-all">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                        <GitBranch className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold">{workflow.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          {workflow.description || "No description"}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-4">
                      <div className="hidden md:flex items-center gap-6 text-sm text-muted-foreground">
                        <Badge variant={status?.variant || "secondary"}>
                          <StatusIcon className="mr-1 h-3 w-3" />
                          {status?.label || workflow.status}
                        </Badge>
                        <div>{workflow.nodes?.length ?? 0} nodes</div>
                        <div>{workflow.execution_count} runs</div>
                        <div>
                          Last:{" "}
                          {workflow.last_executed_at
                            ? formatRelativeTime(workflow.last_executed_at)
                            : "Never"}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        {workflow.status === "active" && (
                          <Button
                            size="sm"
                            onClick={() =>
                              executeMutation.mutate({
                                id: workflow.id,
                                data: { input_data: {} },
                              })
                            }
                            disabled={executeMutation.isPending}
                          >
                            <Play className="mr-1 h-3 w-3" />
                            Run
                          </Button>
                        )}
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                            >
                              <MoreHorizontal className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => setEditingWorkflow(workflow)}
                            >
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              className="text-destructive"
                              onClick={() => {
                                if (confirm(`Delete "${workflow.name}"?`)) {
                                  deleteMutation.mutate(workflow.id);
                                }
                              }}
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <WorkflowDialog
        open={isCreateOpen}
        onOpenChange={setIsCreateOpen}
        onSubmit={(data) => createMutation.mutate(data)}
        isLoading={createMutation.isPending}
      />

      {editingWorkflow && (
        <WorkflowDialog
          open={!!editingWorkflow}
          onOpenChange={() => setEditingWorkflow(null)}
          initialData={editingWorkflow}
          onSubmit={(data) =>
            workflowsApi
              .updateWorkflow(editingWorkflow.id, data)
              .then(() => {
                queryClient.invalidateQueries({ queryKey: ["workflows"] });
                setEditingWorkflow(null);
                toast.success("Workflow updated");
              })
          }
          isLoading={false}
        />
      )}
    </div>
  );
}

function WorkflowDialog({
  open,
  onOpenChange,
  onSubmit,
  isLoading,
  initialData,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: {
    name: string;
    description?: string;
    nodes: Workflow["nodes"];
    edges: Workflow["edges"];
  }) => void;
  isLoading: boolean;
  initialData?: Workflow;
}) {
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");

  React.useEffect(() => {
    if (open) {
      setName(initialData?.name || "");
      setDescription(initialData?.description || "");
    }
  }, [open, initialData]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {initialData ? "Edit Workflow" : "Create Workflow"}
          </DialogTitle>
          <DialogDescription>
            {initialData
              ? "Update your workflow details"
              : "Create a new automated workflow"}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={() =>
              onSubmit({
                name,
                description: description || undefined,
                nodes: initialData?.nodes || [],
                edges: initialData?.edges || [],
              })
            }
            disabled={!name.trim() || isLoading}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {initialData ? "Save Changes" : "Create"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
