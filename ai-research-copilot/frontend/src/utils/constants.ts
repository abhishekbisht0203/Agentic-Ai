export const APP_NAME = "AI Research Copilot";
export const APP_DESCRIPTION = "Enterprise Agentic AI Research Platform";

export const NAV_ITEMS = {
  main: [
    { label: "Dashboard", href: "/dashboard", icon: "LayoutDashboard" },
    { label: "AI Chat", href: "/chat", icon: "MessageSquare" },
    { label: "Knowledge Base", href: "/knowledge", icon: "BookOpen" },
    { label: "Documents", href: "/documents", icon: "FileText" },
    { label: "Agents", href: "/agents", icon: "Bot" },
    { label: "Workflows", href: "/workflows", icon: "GitBranch" },
  ],
  analytics: [
    { label: "Overview", href: "/analytics", icon: "BarChart3" },
    { label: "Reports", href: "/analytics/reports", icon: "FileBarChart" },
    { label: "CSV Analysis", href: "/analytics/csv", icon: "Table" },
    { label: "Excel Analysis", href: "/analytics/excel", icon: "Sheet" },
  ],
  settings: [
    { label: "General", href: "/settings", icon: "Settings" },
    { label: "Organization", href: "/settings/organization", icon: "Building2" },
    { label: "Teams", href: "/settings/teams", icon: "Users" },
    { label: "Billing", href: "/settings/billing", icon: "CreditCard" },
    { label: "API Keys", href: "/settings/api-keys", icon: "Key" },
    { label: "Notifications", href: "/settings/notifications", icon: "Bell" },
  ],
  admin: [
    { label: "Admin Dashboard", href: "/admin", icon: "Shield" },
  ],
} as const;

export const AGENT_TYPES = [
  { value: "research", label: "Research Agent", description: "Deep research with citations" },
  { value: "analysis", label: "Analysis Agent", description: "Data analysis and insights" },
  { value: "writing", label: "Writing Agent", description: "Content creation and editing" },
  { value: "coding", label: "Coding Agent", description: "Code generation and review" },
  { value: "custom", label: "Custom Agent", description: "User-defined agent" },
] as const;

export const FILE_TYPES = {
  document: [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf"],
  spreadsheet: [".csv", ".xlsx", ".xls"],
  code: [".js", ".ts", ".py", ".java", ".cpp", ".go", ".rs"],
  image: [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"],
} as const;

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

export const CHART_COLORS = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
  "hsl(var(--chart-4))",
  "hsl(var(--chart-5))",
];
