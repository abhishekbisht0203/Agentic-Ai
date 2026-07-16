"use client";

import * as React from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Plus,
  Search,
  Bot,
  Loader2,
  AlertTriangle,
  Settings2,
  Trash2,
  Copy,
  Power,
  PowerOff,
  Play,
  MoreHorizontal,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";
import { agentPlatformApi } from "@/services/api/agent-platform";
import type { AgentWithStats, AgentCreate, ProviderInfo, ToolInfo } from "@/types/agent-platform";
import { formatRelativeTime } from "@/utils/helpers";

const DEFAULT_SYSTEM_PROMPTS: Record<string, string> = {
  planner: "Break complex problems into actionable step-by-step plans. Analyze goals, identify dependencies, and produce clear roadmaps.",
  research: "Find, evaluate, and synthesize information. Produce well-structured research summaries with key findings and sources.",
  code_assistant: "Write, explain, debug, and review code. Follow best practices with clear variable names and edge case handling.",
  document_qa: "Answer questions based on uploaded documents using RAG. Cite specific source material and indicate when information is not available.",
  automation: "Design workflows and automate repetitive tasks. Break processes into steps and identify automation opportunities.",
  memory: "Store, organize, and recall user context and preferences. Track important facts and conversation history.",
  critic: "Review responses for weaknesses, gaps, and improvements. Provide constructive, specific feedback.",
  data_analyst: "Analyze CSV, Excel, and JSON data. Identify trends, patterns, and anomalies with statistical evidence.",
  general: "Help with a wide range of tasks. Be helpful, accurate, and concise. Ask clarifying questions when needed.",
};

const ICON_OPTIONS = ["Bot", "Sparkles", "Brain", "Zap", "Globe", "BookOpen", "FileText", "Code", "BarChart3", "Shield"];

const AGENT_PRESETS = [
  { value: "planner", label: "Planner Agent", icon: "ClipboardList" },
  { value: "research", label: "Research Agent", icon: "Search" },
  { value: "code_assistant", label: "Code Assistant", icon: "Code" },
  { value: "document_qa", label: "Document Q&A", icon: "FileText" },
  { value: "automation", label: "Automation Agent", icon: "Zap" },
  { value: "memory", label: "Memory Agent", icon: "BookOpen" },
  { value: "critic", label: "Critic Agent", icon: "Shield" },
  { value: "data_analyst", label: "Data Analyst", icon: "BarChart3" },
  { value: "general", label: "General Agent", icon: "Bot" },
];

export default function AgentsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [showCreate, setShowCreate] = React.useState(false);
  const [editAgent, setEditAgent] = React.useState<AgentWithStats | null>(null);
  const [deleteAgent, setDeleteAgent] = React.useState<AgentWithStats | null>(null);
  const [duplicateAgent, setDuplicateAgent] = React.useState<AgentWithStats | null>(null);

  const agentsQuery = useQuery({
    queryKey: ["agent-platform", "list", search],
    queryFn: () => agentPlatformApi.listAgents({ search: search || undefined }),
  });

  const providersQuery = useQuery({
    queryKey: ["agent-providers"],
    queryFn: () => agentPlatformApi.getProviders(),
  });

  const toolsQuery = useQuery({
    queryKey: ["agent-tools"],
    queryFn: () => agentPlatformApi.getTools(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => agentPlatformApi.deleteAgent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-platform"] });
      toast.success("Agent deleted");
      setDeleteAgent(null);
    },
    onError: () => toast.error("Failed to delete agent"),
  });

  const duplicateMutation = useMutation({
    mutationFn: (id: string) => agentPlatformApi.duplicateAgent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-platform"] });
      toast.success("Agent duplicated");
      setDuplicateAgent(null);
    },
    onError: () => toast.error("Failed to duplicate agent"),
  });

  const toggleMutation = useMutation({
    mutationFn: (id: string) => agentPlatformApi.toggleAgent(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agent-platform"] });
    },
    onError: () => toast.error("Failed to toggle agent"),
  });

  const agents = agentsQuery.data?.items ?? [];
  const agentsLoading = agentsQuery.isLoading;
  const providers = providersQuery.data ?? [];
  const tools = toolsQuery.data ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">AI Agents</h1>
          <p className="text-muted-foreground">Create and manage your AI agents</p>
        </div>
        <Button onClick={() => setShowCreate(true)}>
          <Plus className="mr-2 h-4 w-4" /> Create Agent
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search agents by name, model, or description..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-9"
        />
      </div>

      {agentsQuery.error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>Failed to load agents. Please try again.</AlertDescription>
        </Alert>
      )}

      {agentsLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Card key={i}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <Skeleton className="h-6 w-16 rounded-full" />
                </div>
                <Skeleton className="h-5 w-32 mt-2" />
                <Skeleton className="h-4 w-full mt-1" />
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-2">
                  {Array.from({ length: 3 }).map((_, j) => (
                    <Skeleton key={j} className="h-10 w-full rounded-lg" />
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : agents.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center py-12">
            <Bot className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-lg font-medium">{search ? "No agents match your search" : "No agents yet"}</p>
            <p className="text-sm text-muted-foreground mb-4">
              {search ? "Try a different search term" : "Create your first AI agent to get started"}
            </p>
            {!search && (
              <Button onClick={() => setShowCreate(true)}>
                <Plus className="mr-2 h-4 w-4" /> Create Agent
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <AgentCardComponent
              key={agent.id}
              agent={agent}
              onEdit={setEditAgent}
              onDelete={setDeleteAgent}
              onDuplicate={setDuplicateAgent}
              onToggle={(id) => toggleMutation.mutate(id)}
            />
          ))}
        </div>
      )}

      <CreateEditAgentDialog
        open={showCreate || !!editAgent}
        onOpenChange={(open) => { if (!open) { setShowCreate(false); setEditAgent(null); } }}
        editAgent={editAgent}
        providers={providers}
        tools={tools}
      />

      <Dialog open={!!deleteAgent} onOpenChange={(o) => { if (!o) setDeleteAgent(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Agent</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete &ldquo;{deleteAgent?.name}&rdquo;? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteAgent(null)}>Cancel</Button>
            <Button
              variant="destructive"
              onClick={() => deleteAgent && deleteMutation.mutate(deleteAgent.id)}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!duplicateAgent} onOpenChange={(o) => { if (!o) setDuplicateAgent(null); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Duplicate Agent</DialogTitle>
            <DialogDescription>
              Create a copy of &ldquo;{duplicateAgent?.name}&rdquo;
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDuplicateAgent(null)}>Cancel</Button>
            <Button
              onClick={() => duplicateAgent && duplicateMutation.mutate(duplicateAgent.id)}
              disabled={duplicateMutation.isPending}
            >
              {duplicateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Copy className="mr-2 h-4 w-4" />}
              Duplicate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function AgentCardComponent({
  agent,
  onEdit,
  onDelete,
  onDuplicate,
  onToggle,
}: {
  agent: AgentWithStats;
  onEdit: (a: AgentWithStats) => void;
  onDelete: (a: AgentWithStats) => void;
  onDuplicate: (a: AgentWithStats) => void;
  onToggle: (id: string) => void;
}) {
  return (
    <Card className="hover:shadow-md transition-all">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div
            className="flex h-10 w-10 items-center justify-center rounded-lg"
            style={{ backgroundColor: agent.color + "20" }}
          >
            <Bot className="h-5 w-5" style={{ color: agent.color }} />
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={agent.status === "active" ? "success" : "secondary"} className="text-[10px]">
              {agent.status}
            </Badge>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="h-8 w-8">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={() => onEdit(agent)}>
                  <Settings2 className="mr-2 h-4 w-4" /> Configure
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => onDuplicate(agent)}>
                  <Copy className="mr-2 h-4 w-4" /> Duplicate
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onToggle(agent.id)}>
                  {agent.status === "active" ? (
                    <><PowerOff className="mr-2 h-4 w-4" /> Deactivate</>
                  ) : (
                    <><Power className="mr-2 h-4 w-4" /> Activate</>
                  )}
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => onDelete(agent)} className="text-destructive">
                  <Trash2 className="mr-2 h-4 w-4" /> Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
        <div className="mt-2">
          <div className="flex items-center gap-2">
            <Link href={`/agents/${agent.id}`} className="hover:underline">
              <CardTitle className="text-base">{agent.name}</CardTitle>
            </Link>
          </div>
          <CardDescription className="line-clamp-2 mt-1">
            {agent.description || "No description"}
          </CardDescription>
        </div>
        <div className="flex flex-wrap gap-1 mt-2">
          <Badge variant="outline" className="text-[10px]">{agent.model?.split("/").pop()}</Badge>
          <Badge variant="outline" className="text-[10px] capitalize">{agent.provider}</Badge>
          {agent.rag_enabled && <Badge variant="outline" className="text-[10px]">RAG</Badge>}
          {agent.memory_enabled && <Badge variant="outline" className="text-[10px]">Memory</Badge>}
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="rounded-lg bg-muted p-2 text-center">
            <p className="text-lg font-bold">{agent.total_runs}</p>
            <p className="text-[10px] text-muted-foreground">Runs</p>
          </div>
          <div className="rounded-lg bg-muted p-2 text-center">
            <p className="text-lg font-bold">{agent.success_rate}%</p>
            <p className="text-[10px] text-muted-foreground">Success</p>
          </div>
          <div className="rounded-lg bg-muted p-2 text-center">
            <p className="text-lg font-bold">{agent.avg_latency_ms < 1000 ? `${agent.avg_latency_ms}ms` : `${(agent.avg_latency_ms / 1000).toFixed(1)}s`}</p>
            <p className="text-[10px] text-muted-foreground">Avg Time</p>
          </div>
        </div>
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
          <span>{(agent.total_tokens || 0).toLocaleString()} tokens</span>
          <span>${(agent.total_cost || 0).toFixed(4)}</span>
          {agent.last_run_at && <span>{formatRelativeTime(agent.last_run_at)}</span>}
        </div>
        <div className="flex gap-2">
          <Button size="sm" className="flex-1" disabled={agent.status !== "active"} asChild>
            <Link href={`/agents/${agent.id}/chat`}>
              <Play className="mr-1 h-3 w-3" /> Run
            </Link>
          </Button>
          <Button size="sm" variant="outline" className="flex-1" onClick={() => onEdit(agent)}>
            <Settings2 className="mr-1 h-3 w-3" /> Edit
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function CreateEditAgentDialog({
  open,
  onOpenChange,
  editAgent,
  providers,
  tools,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  editAgent: AgentWithStats | null;
  providers: ProviderInfo[];
  tools: ToolInfo[];
}) {
  const queryClient = useQueryClient();
  const [name, setName] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [systemPrompt, setSystemPrompt] = React.useState("");
  const [agentType, setAgentType] = React.useState("general");
  const [model, setModel] = React.useState("openai/gpt-oss-120b:free");
  const [provider, setProvider] = React.useState("openrouter");
  const [temperature, setTemperature] = React.useState("0.7");
  const [maxTokens, setMaxTokens] = React.useState("4096");
  const [topP, setTopP] = React.useState("1.0");
  const [color, setColor] = React.useState("#6366f1");
  const [icon, setIcon] = React.useState("Bot");
  const [memoryEnabled, setMemoryEnabled] = React.useState(false);
  const [ragEnabled, setRagEnabled] = React.useState(false);
  const [enabledTools, setEnabledTools] = React.useState<string[]>([]);
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    if (editAgent) {
      setName(editAgent.name);
      setDescription(editAgent.description || "");
      setSystemPrompt(editAgent.system_prompt || "");
      setModel(editAgent.model);
      setProvider(editAgent.provider);
      setTemperature(String(editAgent.temperature));
      setMaxTokens(String(editAgent.max_tokens));
      setTopP(String(editAgent.top_p));
      setColor(editAgent.color);
      setIcon(editAgent.icon);
      setMemoryEnabled(editAgent.memory_enabled);
      setRagEnabled(editAgent.rag_enabled);
      setEnabledTools(editAgent.tools_enabled || []);
    } else {
      setName("");
      setDescription("");
      setSystemPrompt("");
      setAgentType("general");
      setModel("openai/gpt-oss-120b:free");
      setProvider("openrouter");
      setTemperature("0.7");
      setMaxTokens("4096");
      setTopP("1.0");
      setColor("#6366f1");
      setIcon("Bot");
      setMemoryEnabled(false);
      setRagEnabled(false);
      setEnabledTools([]);
    }
  }, [editAgent, open]);

  const handlePreset = (type: string) => {
    setAgentType(type);
    setSystemPrompt(DEFAULT_SYSTEM_PROMPTS[type] || "");
    const preset = AGENT_PRESETS.find((p) => p.value === type);
    if (preset) setIcon(preset.icon === "ClipboardList" ? "Sparkles" : preset.icon);
  };

  const toggleTool = (tool: string) => {
    setEnabledTools((prev) =>
      prev.includes(tool) ? prev.filter((t) => t !== tool) : [...prev, tool]
    );
  };

  const handleSave = async () => {
    if (!name.trim()) {
      toast.error("Agent name is required");
      return;
    }
    setSaving(true);
    try {
      const data: AgentCreate = {
        name: name.trim(),
        description: description.trim() || undefined,
        system_prompt: systemPrompt.trim() || undefined,
        model,
        provider,
        temperature: parseFloat(temperature),
        max_tokens: parseInt(maxTokens),
        top_p: parseFloat(topP),
        color,
        icon,
        memory_enabled: memoryEnabled,
        rag_enabled: ragEnabled,
        tools_enabled: enabledTools.length > 0 ? enabledTools : undefined,
        status: "active",
      };

      if (editAgent) {
        await agentPlatformApi.updateAgent(editAgent.id, data);
        toast.success("Agent updated");
      } else {
        await agentPlatformApi.createAgent(data);
        toast.success("Agent created");
      }
      queryClient.invalidateQueries({ queryKey: ["agent-platform"] });
      onOpenChange(false);
    } catch {
      toast.error(editAgent ? "Failed to update agent" : "Failed to create agent");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editAgent ? "Edit Agent" : "Create Agent"}</DialogTitle>
          <DialogDescription>
            {editAgent ? "Modify your agent's configuration" : "Configure a new AI agent with custom settings"}
          </DialogDescription>
        </DialogHeader>

        {!editAgent && (
          <div className="space-y-2">
            <Label>Quick Start Templates</Label>
            <div className="flex flex-wrap gap-2">
              {AGENT_PRESETS.map((p) => (
                <Button
                  key={p.value}
                  variant={agentType === p.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => handlePreset(p.value)}
                  className="text-xs"
                >
                  {p.label}
                </Button>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Agent Name *</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="My Research Agent" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="color">Color</Label>
              <div className="flex items-center gap-2">
                <input
                  type="color"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  className="h-9 w-9 rounded cursor-pointer"
                />
                <Select value={icon} onValueChange={setIcon}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {ICON_OPTIONS.map((ic) => (
                      <SelectItem key={ic} value={ic}>{ic}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="desc">Description</Label>
            <Textarea
              id="desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What does this agent do?"
              className="resize-none"
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="prompt">System Prompt</Label>
            <Textarea
              id="prompt"
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              placeholder="Define the agent's behavior and instructions..."
              className="resize-none font-mono text-xs"
              rows={6}
            />
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="provider">Provider</Label>
              <Select value={provider} onValueChange={setProvider}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {providers.map((p) => (
                    <SelectItem key={p.value} value={p.value}>
                      {p.label} {p.free && "(Free)"}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="model">Model</Label>
              <Input id="model" value={model} onChange={(e) => setModel(e.target.value)} placeholder="model/id" />
            </div>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="temp">Temperature</Label>
              <Input id="temp" type="number" min="0" max="2" step="0.1" value={temperature} onChange={(e) => setTemperature(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tokens">Max Tokens</Label>
              <Input id="tokens" type="number" min="1" step="1" value={maxTokens} onChange={(e) => setMaxTokens(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="topp">Top P</Label>
              <Input id="topp" type="number" min="0" max="1" step="0.1" value={topP} onChange={(e) => setTopP(e.target.value)} />
            </div>
          </div>

          <div className="space-y-3">
            <Label>Capabilities</Label>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div><p className="text-sm font-medium">Memory</p><p className="text-xs text-muted-foreground">Store and recall conversation context</p></div>
              <Switch checked={memoryEnabled} onCheckedChange={setMemoryEnabled} />
            </div>
            <div className="flex items-center justify-between rounded-lg border p-3">
              <div><p className="text-sm font-medium">RAG (Knowledge Base)</p><p className="text-xs text-muted-foreground">Retrieve relevant information from documents</p></div>
              <Switch checked={ragEnabled} onCheckedChange={setRagEnabled} />
            </div>
          </div>

          {tools.length > 0 && (
            <div className="space-y-3">
              <Label>Tools</Label>
              <div className="grid gap-2 md:grid-cols-2">
                {tools.map((tool) => (
                  <div
                    key={tool.value}
                    className={`flex items-center justify-between rounded-lg border p-2 cursor-pointer transition-colors ${
                      enabledTools.includes(tool.value) ? "border-primary bg-primary/5" : ""
                    }`}
                    onClick={() => toggleTool(tool.value)}
                  >
                    <div>
                      <p className="text-sm font-medium">{tool.label}</p>
                      <p className="text-xs text-muted-foreground">{tool.description}</p>
                    </div>
                    <Switch
                      checked={enabledTools.includes(tool.value)}
                      onCheckedChange={() => toggleTool(tool.value)}
                    />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSave} disabled={saving}>
            {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
            {editAgent ? "Save Changes" : "Create Agent"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
