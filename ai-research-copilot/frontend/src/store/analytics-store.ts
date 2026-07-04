import { create } from "zustand";
import type {
  AnalyticsState,
  AnalyticsSummary,
  AnalyticsReport,
  Visualization,
  UserActivity,
} from "@/types";

export const useAnalyticsStore = create<AnalyticsState>((set) => ({
  summary: null,
  reports: [],
  visualizations: [],
  activities: [],
  isLoading: false,
  error: null,

  setSummary: (summary: AnalyticsSummary) => set({ summary }),
  setReports: (reports: AnalyticsReport[]) => set({ reports }),
  setVisualizations: (visualizations: Visualization[]) =>
    set({ visualizations }),
  setActivities: (activities: UserActivity[]) => set({ activities }),
  setIsLoading: (isLoading: boolean) => set({ isLoading }),
  setError: (error: string | null) => set({ error }),
}));
