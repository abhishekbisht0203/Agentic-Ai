import { create } from "zustand";
import type { WorkflowState, Workflow, WorkflowDetail } from "@/types";

export const useWorkflowStore = create<WorkflowState>((set) => ({
  workflows: [],
  currentWorkflow: null,
  isLoading: false,
  error: null,

  setWorkflows: (workflows: Workflow[]) => set({ workflows }),
  setCurrentWorkflow: (workflow: WorkflowDetail | null) =>
    set({ currentWorkflow: workflow }),
  setIsLoading: (isLoading: boolean) => set({ isLoading }),
  setError: (error: string | null) => set({ error }),
}));
