import apiClient from "./client";

export interface AppInfo {
  app_name: string;
  version: string;
  environment: string;
  features: Record<string, boolean>;
}

export interface SettingsPreferences {
  theme: string;
  language: string;
  timezone: string;
  notifications_email: boolean;
  notifications_tasks: boolean;
  notifications_documents: boolean;
  notifications_weekly: boolean;
  compact_view: boolean;
  default_model: string;
  default_temperature: number;
  default_max_tokens: number;
}

export const settingsApi = {
  getPreferences: async (): Promise<SettingsPreferences> => {
    const response = await apiClient.get<SettingsPreferences>("/settings/preferences");
    return response.data;
  },

  updatePreferences: async (
    data: Partial<SettingsPreferences>
  ): Promise<SettingsPreferences> => {
    const response = await apiClient.put<SettingsPreferences>(
      "/settings/preferences",
      data
    );
    return response.data;
  },

  getInfo: async (): Promise<AppInfo> => {
    const response = await apiClient.get<AppInfo>("/settings/info");
    return response.data;
  },
};
