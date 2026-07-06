"use client";

import * as React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { useAgents } from "@/hooks/use-agents";
import { AgentCard } from "@/components/agents/agent-card";
import { agentsApi } from "@/services/api/agents";
import { toast } from "sonner";
import { AGENT_TYPES } from "@/utils/constants";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { AgentConfiguration } from "@/types";

export default function AgentsPage() {
  const queryClient = useQueryClient();
  const {
    configurations,
    isLoading,
    deleteConfiguration,
    updateConfiguration,
  } = useAgents();

  const [isCreateOpen, setIsCreateOpen] = React.useState(false);
  const [executingAgent, setExecutingAgent] = React.useState<AgentConfiguration | null>(null);
  const [createName, setCreateName] = React.useState("");
  const [createDescription, setCreateDescription] = React.useState("");
  const [createAgentType, setCreateAgentType] = React.useState("");
  const [createModel, setCreateModel] = React.useState("");
  const [createSystemPrompt, setCreateSystemPrompt] = React.useState("");

  const createMutation = useMutation({
    mutationFn: agentsApi.createConfiguration,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-configurations"] });
      setIsCreateOpen(false);
      setCreateName("");
      setCreateDescription("");
      setCreateAgentType("");
      setCreateModel("");
      setCreateSystemPrompt("");
      toast.success("Agent created");
    },
    onError: () => {
      toast.error("Failed to create agent");
    },
  });

  const executeMutation = useMutation({
    mutationFn: agentsApi.executeAgent,
    onSuccess: () => {
      setExecutingAgent(null);
      toast.success("Agent execution started");
    },
    onError: () => {
      toast.error("Failed to execute agent");
    },
  });

  const handleDelete = (agent: AgentConfiguration) => {
    if (confirm(`Delete "${agent.name}"?`)) {
      deleteConfiguration.mutate(agent.id);
    }
  };

  const handleToggle = (agent: AgentConfiguration, active: boolean) => {
    updateConfiguration.mutate({
      id: agent.id,
      data: { is_active: active },
    });
  };

  const handleCreate = () => {
    if (!createName.trim() || !createAgentType || !createModel.trim()) {
      toast.error("Please fill in all required fields");
      return;
    }
    createMutation.mutate({
      name: createName,
      description: createDescription || null,
      agent_type: createAgentType,
      model: createModel,
      system_prompt: createSystemPrompt || null,
      temperature: 0.7,
      max_tokens: 4096,
      tools: [],
      is_active: true,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Agents</h1>
          <p className="text-muted-foreground">
            Configure and manage your AI agents
          </p>
        </div>
        <Button onClick={() => setIsCreateOpen(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Create Agent
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="rounded-lg border bg-card p-6">
              <div className="flex items-start gap-3">
                <Skeleton className="h-10 w-10 rounded-lg" />
                <div className="flex-1 space-y-1">
                  <Skeleton className="h-5 w-32" />
                  <Skeleton className="h-3 w-full" />
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : configurations.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-muted-foreground">
            No agents configured yet. Create one to get started.
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {configurations.map((agent: AgentConfiguration) => (
            <AgentCard
              key={agent.id}
              agent={agent}
              onExecute={() => setExecutingAgent(agent)}
              onDelete={handleDelete}
              onToggle={handleToggle}
            />
          ))}
        </div>
      )}

      <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Create Agent</DialogTitle>
            <DialogDescription>
              Configure a new AI agent for your platform
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={createName}
                onChange={(e) => setCreateName(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={createDescription}
                onChange={(e) => setCreateDescription(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Agent Type</Label>
              <Select value={createAgentType} onValueChange={setCreateAgentType}>
                <SelectTrigger>
                  <SelectValue placeholder="Select agent type" />
                </SelectTrigger>
                <SelectContent>
                  {AGENT_TYPES.map((type) => (
                    <SelectItem key={type.value} value={type.value}>
                      {type.label} - {type.description}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="model">Model</Label>
              <Input
                id="model"
                placeholder="gpt-4o"
                value={createModel}
                onChange={(e) => setCreateModel(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="system_prompt">System Prompt</Label>
              <Textarea
                id="system_prompt"
                placeholder="You are ARC, an AI Research Copilot..."
                value={createSystemPrompt}
                onChange={(e) => setCreateSystemPrompt(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreate} disabled={createMutation.isPending}>
              {createMutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Agent
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {executingAgent && (
        <ExecuteAgentDialog
          agent={executingAgent}
          open={!!executingAgent}
          onOpenChange={() => setExecutingAgent(null)}
          onSubmit={(data) =>
            executeMutation.mutate({
              agent_type: executingAgent.agent_type,
              input_data: data,
            })
          }
          isLoading={executeMutation.isPending}
        />
      )}
    </div>
  );
}

function ExecuteAgentDialog({
  agent,
  open,
  onOpenChange,
  onSubmit,
  isLoading,
}: {
  agent: AgentConfiguration;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: Record<string, unknown>) => void;
  isLoading: boolean;
}) {
  const [inputData, setInputData] = React.useState("");

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Execute {agent.name}</DialogTitle>
          <DialogDescription>
            Provide input data for the agent to process
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Agent Type</Label>
            <p className="text-sm text-muted-foreground">{agent.agent_type}</p>
          </div>
          <div className="space-y-2">
            <Label>Model</Label>
            <p className="text-sm text-muted-foreground">{agent.model}</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="input">Input Data (JSON)</Label>
            <Textarea
              id="input"
              placeholder='{"query": "Your input here"}'
              value={inputData}
              onChange={(e) => setInputData(e.target.value)}
              rows={4}
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={() => {
              try {
                const data = inputData ? JSON.parse(inputData) : {};
                onSubmit(data);
              } catch {
                toast.error("Invalid JSON input");
              }
            }}
            disabled={isLoading}
          >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Execute
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
