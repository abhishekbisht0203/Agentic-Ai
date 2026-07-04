"use client";

import * as React from "react";
import { useDropzone } from "react-dropzone";
import {
  Upload,
  FileText,
  X,
  CheckCircle2,
  AlertCircle,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { cn, formatBytes } from "@/utils/helpers";
import { MAX_FILE_SIZE, FILE_TYPES } from "@/utils/constants";
import { useDocuments } from "@/hooks/use-documents";
import { toast } from "sonner";

const acceptedFileTypes: Record<string, string[]> = {
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "text/plain": [".txt"],
  "text/markdown": [".md"],
  "text/csv": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel": [".xls"],
};

interface DocumentUploadProps {
  onUploadComplete?: () => void;
  knowledgeBaseIds?: string[];
  className?: string;
}

export function DocumentUpload({
  onUploadComplete,
  knowledgeBaseIds,
  className,
}: DocumentUploadProps) {
  const { uploadDocument, uploadQueue, clearUploadQueue } = useDocuments();

  const onDrop = React.useCallback(
    async (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        if (file.size > MAX_FILE_SIZE) {
          toast.error(`${file.name} exceeds 50MB limit`);
          continue;
        }

        try {
          await uploadDocument.mutateAsync({
            file,
            knowledgeBaseIds,
          });
          toast.success(`${file.name} uploaded successfully`);
        } catch {
          toast.error(`Failed to upload ${file.name}`);
        }
      }
      onUploadComplete?.();
    },
    [uploadDocument, knowledgeBaseIds, onUploadComplete]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: acceptedFileTypes,
    maxSize: MAX_FILE_SIZE,
    multiple: true,
  });

  return (
    <div className={cn("space-y-4", className)}>
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors",
          isDragActive
            ? "border-primary bg-primary/5"
            : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/20"
        )}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center gap-3">
          <div
            className={cn(
              "flex h-12 w-12 items-center justify-center rounded-full transition-colors",
              isDragActive ? "bg-primary/10" : "bg-muted"
            )}
          >
            <Upload
              className={cn(
                "h-6 w-6 transition-colors",
                isDragActive ? "text-primary" : "text-muted-foreground"
              )}
            />
          </div>
          <div>
            <p className="text-sm font-medium">
              {isDragActive
                ? "Drop files here"
                : "Drag & drop files here, or click to browse"}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Supports PDF, DOCX, TXT, MD, CSV, XLSX (max 50MB)
            </p>
          </div>
        </div>
      </div>

      {uploadQueue.length > 0 && (
        <div className="space-y-2">
          {uploadQueue.map((item) => (
            <div
              key={item.id}
              className="flex items-center gap-3 rounded-lg border p-3"
            >
              <FileText className="h-5 w-5 text-muted-foreground shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-medium truncate">{item.file.name}</p>
                  <span className="text-xs text-muted-foreground">
                    {formatBytes(item.file.size)}
                  </span>
                </div>
                {item.status === "uploading" && (
                  <Progress value={item.progress} className="mt-2 h-1.5" />
                )}
                {item.status === "completed" && (
                  <div className="flex items-center gap-1 mt-1">
                    <CheckCircle2 className="h-3 w-3 text-emerald-500" />
                    <span className="text-xs text-emerald-500">Uploaded</span>
                  </div>
                )}
                {item.status === "error" && (
                  <div className="flex items-center gap-1 mt-1">
                    <AlertCircle className="h-3 w-3 text-destructive" />
                    <span className="text-xs text-destructive">
                      {item.error || "Upload failed"}
                    </span>
                  </div>
                )}
              </div>
            </div>
          ))}
          <Button
            variant="ghost"
            size="sm"
            onClick={clearUploadQueue}
            className="w-full"
          >
            Clear completed
          </Button>
        </div>
      )}
    </div>
  );
}
