"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import {
  MessageSquare,
  FileText,
  BookOpen,
  Bot,
  GitBranch,
  BarChart3,
  Settings,
  Search,
  Moon,
  Sun,
  LogOut,
  Command,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
} from "@/components/ui/dialog";
import { useAuthStore } from "@/store/auth-store";

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ElementType;
  action: () => void;
  category: string;
}

export function CommandPalette() {
  const [open, setOpen] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const router = useRouter();
  const { setTheme } = useTheme();
  const { logout } = useAuthStore();

  React.useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const items: CommandItem[] = [
    {
      id: "chat",
      label: "AI Chat",
      description: "Start a new conversation",
      icon: MessageSquare,
      action: () => router.push("/chat"),
      category: "Navigation",
    },
    {
      id: "documents",
      label: "Documents",
      description: "Manage your documents",
      icon: FileText,
      action: () => router.push("/documents"),
      category: "Navigation",
    },
    {
      id: "knowledge",
      label: "Knowledge Base",
      description: "Browse knowledge bases",
      icon: BookOpen,
      action: () => router.push("/knowledge"),
      category: "Navigation",
    },
    {
      id: "agents",
      label: "Agents",
      description: "Configure AI agents",
      icon: Bot,
      action: () => router.push("/agents"),
      category: "Navigation",
    },
    {
      id: "workflows",
      label: "Workflows",
      description: "Manage workflows",
      icon: GitBranch,
      action: () => router.push("/workflows"),
      category: "Navigation",
    },
    {
      id: "analytics",
      label: "Analytics",
      description: "View analytics",
      icon: BarChart3,
      action: () => router.push("/analytics"),
      category: "Navigation",
    },
    {
      id: "settings",
      label: "Settings",
      description: "Platform settings",
      icon: Settings,
      action: () => router.push("/settings"),
      category: "Navigation",
    },
    {
      id: "dark-mode",
      label: "Toggle Dark Mode",
      icon: Moon,
      action: () => setTheme("dark"),
      category: "Theme",
    },
    {
      id: "light-mode",
      label: "Toggle Light Mode",
      icon: Sun,
      action: () => setTheme("light"),
      category: "Theme",
    },
    {
      id: "logout",
      label: "Log Out",
      icon: LogOut,
      action: () => logout(),
      category: "Account",
    },
  ];

  const filteredItems = items.filter(
    (item) =>
      item.label.toLowerCase().includes(query.toLowerCase()) ||
      item.description?.toLowerCase().includes(query.toLowerCase())
  );

  React.useEffect(() => {
    if (!open) {
      setQuery("");
    }
  }, [open]);

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-4 right-4 z-50 flex items-center gap-2 rounded-full border bg-background/95 backdrop-blur px-4 py-2 shadow-lg hover:bg-accent transition-colors"
      >
        <Command className="h-4 w-4 text-muted-foreground" />
        <span className="text-sm text-muted-foreground">Command</span>
        <kbd className="pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="overflow-hidden p-0 max-w-lg">
          <div className="flex items-center border-b px-3">
            <Search className="h-4 w-4 text-muted-foreground shrink-0" />
            <input
              placeholder="Type a command or search..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="flex h-12 w-full rounded-md bg-transparent py-3 pl-2 text-sm outline-none placeholder:text-muted-foreground disabled:cursor-not-allowed disabled:opacity-50"
              autoFocus
            />
          </div>
          <div className="max-h-[300px] overflow-y-auto p-2">
            {filteredItems.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-6">
                No results found
              </p>
            ) : (
              <>
                {Object.entries(
                  filteredItems.reduce(
                    (acc, item) => ({
                      ...acc,
                      [item.category]: [...(acc[item.category] || []), item],
                    }),
                    {} as Record<string, CommandItem[]>
                  )
                ).map(([category, items]) => (
                  <div key={category} className="mb-2">
                    <p className="px-2 py-1.5 text-xs font-medium text-muted-foreground">
                      {category}
                    </p>
                    {items.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => {
                          item.action();
                          setOpen(false);
                        }}
                        className="flex w-full items-center gap-3 rounded-md px-2 py-2 text-sm hover:bg-accent transition-colors"
                      >
                        <item.icon className="h-4 w-4 text-muted-foreground" />
                        <div className="flex-1 text-left">
                          <p className="font-medium">{item.label}</p>
                          {item.description && (
                            <p className="text-xs text-muted-foreground">
                              {item.description}
                            </p>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                ))}
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
