import { create } from "zustand";
import type {
  AgentState,
  AgentConfiguration,
  AgentConfigurationDetail,
} from "@/types";

export const useAgentStore = create<AgentState>((set) => ({
  configurations: [],
  currentConfig: null,
  isLoading: false,
  error: null,

  setConfigurations: (configurations: AgentConfiguration[]) =>
    set({ configurations }),
  setCurrentConfig: (config: AgentConfigurationDetail | null) =>
    set({ currentConfig: config }),
  setIsLoading: (isLoading: boolean) => set({ isLoading }),
  setError: (error: string | null) => set({ error }),
}));
