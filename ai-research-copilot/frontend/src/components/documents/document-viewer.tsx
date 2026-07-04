"use client";

import * as React from "react";
import {
  FileText,
  Download,
  Trash2,
  Clock,
  CheckCircle2,
  AlertCircle,
  Eye,
  X,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { formatBytes, formatDate, cn } from "@/utils/helpers";
import { documentsApi } from "@/services/api/documents";
import type { DocumentDetail, DocumentChunk } from "@/types";

interface DocumentViewerProps {
  documentId: string | null;
  onClose?: () => void;
}

const statusConfig = {
  completed: {
    label: "Indexed",
    variant: "success" as const,
    icon: CheckCircle2,
  },
  processing: {
    label: "Processing",
    variant: "warning" as const,
    icon: Clock,
  },
  failed: {
    label: "Failed",
    variant: "destructive" as const,
    icon: AlertCircle,
  },
  pending: {
    label: "Pending",
    variant: "secondary" as const,
    icon: Clock,
  },
};

export function DocumentViewer({ documentId, onClose }: DocumentViewerProps) {
  const [document, setDocument] = React.useState<DocumentDetail | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState<"details" | "chunks">("details");

  React.useEffect(() => {
    if (!documentId) {
      setDocument(null);
      return;
    }

    const fetchDocument = async () => {
      setIsLoading(true);
      try {
        const doc = await documentsApi.getDocument(documentId);
        setDocument(doc);
      } catch {
        // handled by error boundary
      } finally {
        setIsLoading(false);
      }
    };

    fetchDocument();
  }, [documentId]);

  if (!documentId) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        <p>Select a document to view details</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (!document) return null;

  const status = statusConfig[document.status];
  const StatusIcon = status.icon;

  return (
    <div className="flex h-full flex-col border-l bg-background">
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted shrink-0">
            <FileText className="h-5 w-5 text-muted-foreground" />
          </div>
          <div className="min-w-0">
            <h3 className="font-semibold truncate">{document.name}</h3>
            <p className="text-xs text-muted-foreground truncate">
              {document.original_filename}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={() => documentsApi.downloadDocument(document.id)}
          >
            <Download className="h-4 w-4" />
          </Button>
          {onClose && (
            <Button variant="ghost" size="icon" className="h-8 w-8" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>

      <div className="flex border-b">
        <button
          className={cn(
            "flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors",
            activeTab === "details"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
          onClick={() => setActiveTab("details")}
        >
          Details
        </button>
        <button
          className={cn(
            "flex-1 px-4 py-2 text-sm font-medium border-b-2 transition-colors",
            activeTab === "chunks"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground"
          )}
          onClick={() => setActiveTab("chunks")}
        >
          Chunks ({document.chunks?.length ?? 0})
        </button>
      </div>

      <ScrollArea className="flex-1">
        {activeTab === "details" ? (
          <div className="p-4 space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Status</span>
                <Badge variant={status.variant}>
                  <StatusIcon className="mr-1 h-3 w-3" />
                  {status.label}
                </Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Size</span>
                <span className="text-sm">{formatBytes(document.file_size)}</span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Chunks</span>
                <span className="text-sm">{document.chunk_count}</span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">MIME Type</span>
                <span className="text-sm">{document.mime_type}</span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Created</span>
                <span className="text-sm">{formatDate(document.created_at)}</span>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Updated</span>
                <span className="text-sm">{formatDate(document.updated_at)}</span>
              </div>
            </div>

            {document.knowledge_base_ids?.length > 0 && (
              <>
                <Separator />
                <div>
                  <p className="text-sm font-medium mb-2">Knowledge Bases</p>
                  <div className="flex flex-wrap gap-1">
                    {document.knowledge_base_ids.map((kbId) => (
                      <Badge key={kbId} variant="outline">
                        {kbId}
                      </Badge>
                    ))}
                  </div>
                </div>
              </>
            )}

            {document.error_message && (
              <>
                <Separator />
                <div className="rounded-lg bg-destructive/10 p-3">
                  <p className="text-sm font-medium text-destructive">Error</p>
                  <p className="text-sm text-destructive/80">
                    {document.error_message}
                  </p>
                </div>
              </>
            )}
          </div>
        ) : (
          <div className="p-4 space-y-3">
            {document.chunks?.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                No chunks available
              </p>
            ) : (
              document.chunks?.map((chunk, index) => (
                <ChunkItem key={chunk.id} chunk={chunk} index={index} />
              ))
            )}
          </div>
        )}
      </ScrollArea>
    </div>
  );
}

function ChunkItem({
  chunk,
  index,
}: {
  chunk: DocumentChunk;
  index: number;
}) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <div
      className="rounded-lg border p-3 cursor-pointer hover:bg-muted/50 transition-colors"
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">
          Chunk #{index + 1}
        </span>
        <Badge variant="outline" className="text-[10px]">
          {chunk.token_count} tokens
        </Badge>
      </div>
      <p
        className={cn(
          "text-sm mt-2",
          !expanded && "line-clamp-2"
        )}
      >
        {chunk.content}
      </p>
    </div>
  );
}

function Loader2({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}
