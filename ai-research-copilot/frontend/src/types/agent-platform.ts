export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  system_prompt: string | null;
  avatar: string | null;
  icon: string;
  color: string;
  model: string;
  provider: string;
  temperature: number;
  max_tokens: number;
  top_p: number;
  frequency_penalty: number;
  presence_penalty: number;
  tools_enabled: string[] | null;
  knowledge_base_id: string | null;
  memory_enabled: boolean;
  rag_enabled: boolean;
  workflow_enabled: boolean;
  status: string;
  visibility: string;
  created_at: string;
  updated_at: string;
}

export interface AgentWithStats extends Agent {
  total_runs: number;
  last_run_at: string | null;
  avg_latency_ms: number;
  success_rate: number;
  total_tokens: number;
  total_cost: number;
  active_conversations: number;
}

export interface AgentList {
  items: AgentWithStats[];
  total: number;
}

export interface AgentCreate {
  name: string;
  description?: string;
  system_prompt?: string;
  avatar?: string;
  icon?: string;
  color?: string;
  model?: string;
  provider?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  tools_enabled?: string[];
  knowledge_base_id?: string;
  memory_enabled?: boolean;
  rag_enabled?: boolean;
  workflow_enabled?: boolean;
  status?: string;
  visibility?: string;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  avatar?: string;
  icon?: string;
  color?: string;
  model?: string;
  provider?: string;
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  tools_enabled?: string[];
  knowledge_base_id?: string;
  memory_enabled?: boolean;
  rag_enabled?: boolean;
  workflow_enabled?: boolean;
  status?: string;
  visibility?: string;
}

export interface AgentRun {
  id: string;
  agent_id: string;
  conversation_id: string | null;
  input_text: string | null;
  output_text: string | null;
  tokens_prompt: number;
  tokens_completion: number;
  tokens_total: number;
  latency_ms: number;
  cost_usd: number;
  success: boolean;
  error: string | null;
  model_used: string | null;
  provider_used: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface AgentRunList {
  items: AgentRun[];
  total: number;
}

export interface AgentMemory {
  id: string;
  agent_id: string;
  key: string;
  value: string;
  memory_type: string;
  relevance_score: number;
  created_at: string;
}

export interface AgentTool {
  id: string;
  agent_id: string;
  tool_name: string;
  enabled: boolean;
  config: Record<string, unknown> | null;
}

export interface AgentChatRequest {
  message: string;
  conversation_id?: string;
}

export interface AgentChatResponse {
  conversation_id: string;
  message: string;
  role: string;
  agent_name?: string;
  tokens?: number;
  latency_ms?: number;
}

export interface ProviderInfo {
  value: string;
  label: string;
  default_model: string;
  free: boolean;
}

export interface ToolInfo {
  value: string;
  label: string;
  description: string;
}
