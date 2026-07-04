"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useAgentStore } from "@/store/agent-store";
import { agentsApi } from "@/services/api/agents";
import type { AgentConfiguration } from "@/types";

export function useAgents() {
  const queryClient = useQueryClient();
  const store = useAgentStore();

  const { data, isLoading } = useQuery({
    queryKey: ["agent-configurations"],
    queryFn: () => agentsApi.listConfigurations(),
  });

  const createConfiguration = useMutation({
    mutationFn: (data: Omit<AgentConfiguration, "id" | "created_at" | "updated_at">) =>
      agentsApi.createConfiguration(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-configurations"] });
    },
  });

  const updateConfiguration = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<AgentConfiguration> }) =>
      agentsApi.updateConfiguration(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-configurations"] });
    },
  });

  const deleteConfiguration = useMutation({
    mutationFn: (id: string) => agentsApi.deleteConfiguration(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-configurations"] });
    },
  });

  const executeAgent = useMutation({
    mutationFn: agentsApi.executeAgent,
  });

  return {
    configurations: data?.items ?? [],
    currentConfig: store.currentConfig,
    isLoading,
    error: store.error,
    createConfiguration,
    updateConfiguration,
    deleteConfiguration,
    executeAgent,
    getAgentStatus: agentsApi.getAgentStatus,
  };
}
