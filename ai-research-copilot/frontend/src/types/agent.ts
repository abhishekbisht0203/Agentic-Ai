export interface AgentConfiguration {
  id: string;
  name: string;
  description: string | null;
  agent_type: string;
  model: string;
  system_prompt: string | null;
  temperature: number;
  max_tokens: number;
  tools: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentConfigurationDetail extends AgentConfiguration {
  execution_count: number;
  last_executed_at: string | null;
}

export interface AgentExecuteRequest {
  agent_type: string;
  input_data: Record<string, unknown>;
  conversation_id?: string;
  model?: string;
}

export interface AgentExecuteResponse {
  id: string;
  status: "pending" | "running" | "completed" | "failed";
  output_data: Record<string, unknown> | null;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
  created_at: string;
}

export interface AgentState {
  configurations: AgentConfiguration[];
  currentConfig: AgentConfigurationDetail | null;
  isLoading: boolean;
  error: string | null;
  setConfigurations: (configs: AgentConfiguration[]) => void;
  setCurrentConfig: (config: AgentConfigurationDetail | null) => void;
  setIsLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
}
