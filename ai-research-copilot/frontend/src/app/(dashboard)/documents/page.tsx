"use client";

import * as React from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Plus,
  Search,
  MoreHorizontal,
  Trash2,
  Download,
  Eye,
  Filter,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useDocuments } from "@/hooks/use-documents";
import { DocumentUpload } from "@/components/documents/document-upload";
import { DocumentViewer } from "@/components/documents/document-viewer";
import { formatBytes, formatRelativeTime } from "@/utils/helpers";
import { toast } from "sonner";
import type { Document } from "@/types";

const statusConfig = {
  completed: { label: "Indexed", variant: "success" as const },
  processing: { label: "Processing", variant: "warning" as const },
  failed: { label: "Failed", variant: "destructive" as const },
  pending: { label: "Pending", variant: "secondary" as const },
};

export default function DocumentsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const viewId = searchParams.get("view");
  const [searchQuery, setSearchQuery] = React.useState("");
  const [isUploading, setIsUploading] = React.useState(false);
  const {
    documents,
    total,
    isLoading,
    deleteDocument,
    downloadDocument,
  } = useDocuments();

  const filteredDocuments = documents.filter(
    (doc) =>
      doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      doc.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleDelete = async (doc: Document) => {
    if (confirm(`Delete "${doc.name}"?`)) {
      try {
        await deleteDocument.mutateAsync(doc.id);
        toast.success("Document deleted");
      } catch {
        toast.error("Failed to delete document");
      }
    }
  };

  const handleDownload = async (doc: Document) => {
    try {
      await downloadDocument.mutateAsync(doc.id);
    } catch {
      toast.error("Failed to download document");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Documents</h1>
          <p className="text-muted-foreground">
            Upload and manage your documents for AI analysis
          </p>
        </div>
        <Button onClick={() => setIsUploading(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Upload Document
        </Button>
      </div>

      <DocumentUpload />

      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>All Documents</CardTitle>
              <CardDescription>
                {total} documents total
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search documents..."
                  className="pl-9 w-64"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center gap-3">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="flex-1 space-y-1">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-3 w-24" />
                  </div>
                  <Skeleton className="h-6 w-16" />
                </div>
              ))}
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Size</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Chunks</TableHead>
                  <TableHead>Uploaded</TableHead>
                  <TableHead className="w-12" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDocuments.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      {searchQuery ? "No documents match your search" : "No documents uploaded yet"}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredDocuments.map((doc) => {
                    const status = statusConfig[doc.status];
                    return (
                      <TableRow key={doc.id}>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                              <span className="text-xs font-medium text-muted-foreground">
                                {doc.original_filename.split(".").pop()?.toUpperCase()}
                              </span>
                            </div>
                            <div>
                              <p className="font-medium">{doc.name}</p>
                              <p className="text-sm text-muted-foreground">
                                {doc.original_filename}
                              </p>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>{formatBytes(doc.file_size)}</TableCell>
                        <TableCell>
                          <Badge variant={statusConfig[doc.status as keyof typeof statusConfig]?.variant ?? "secondary"}>
                            {statusConfig[doc.status as keyof typeof statusConfig]?.label ?? doc.status}
                          </Badge>
                        </TableCell>
                        <TableCell>{doc.chunk_count}</TableCell>
                        <TableCell>{formatRelativeTime(doc.created_at)}</TableCell>
                        <TableCell>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                <MoreHorizontal className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => router.push(`/documents?view=${doc.id}`)}
                              >
                                <Eye className="mr-2 h-4 w-4" />
                                View Details
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleDownload(doc)}>
                                <Download className="mr-2 h-4 w-4" />
                                Download
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-destructive"
                                onClick={() => handleDelete(doc)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={!!viewId} onOpenChange={() => router.push("/documents")}>
        <DialogContent className="max-w-2xl h-[80vh] p-0">
          <DocumentViewer
            documentId={viewId}
            onClose={() => router.push("/documents")}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
