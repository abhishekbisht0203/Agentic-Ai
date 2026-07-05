"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  FileText,
  Image,
  FileSpreadsheet,
  File,
  FileCode,
  Archive,
  Play,
  Pause,
  Trash2,
  Send,
} from "lucide-react";

interface AttachmentItem {
  id: string;
  file: File;
  preview?: string;
}

interface AttachmentPreviewProps {
  attachments: AttachmentItem[];
  onRemove: (id: string) => void;
}

function getFileIcon(fileName: string) {
  const ext = fileName.split(".").pop()?.toLowerCase() ?? "";
  if (["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext))
    return <Image className="h-4 w-4 text-blue-400" />;
  if (["pdf"].includes(ext))
    return <FileText className="h-4 w-4 text-red-400" />;
  if (["doc", "docx"].includes(ext))
    return <FileText className="h-4 w-4 text-blue-300" />;
  if (["xls", "xlsx", "csv"].includes(ext))
    return <FileSpreadsheet className="h-4 w-4 text-green-400" />;
  if (["js", "ts", "tsx", "jsx", "py", "rb", "go", "rs"].includes(ext))
    return <FileCode className="h-4 w-4 text-yellow-400" />;
  if (["zip", "tar", "gz", "7z", "rar"].includes(ext))
    return <Archive className="h-4 w-4 text-purple-400" />;
  if (["md"].includes(ext))
    return <FileCode className="h-4 w-4 text-cyan-400" />;
  return <File className="h-4 w-4 text-muted-foreground" />;
}

function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

export function AttachmentPreview({ attachments, onRemove }: AttachmentPreviewProps) {
  if (attachments.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 px-1" role="list" aria-label="Attachments">
      <AnimatePresence mode="popLayout">
        {attachments.map((att) => (
          <motion.div
            key={att.id}
            initial={{ opacity: 0, scale: 0.8, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: -8 }}
            transition={{ type: "spring", stiffness: 400, damping: 25 }}
            className="relative flex items-center gap-2 rounded-xl border border-[#2D3748] bg-[#1F2937] px-3 py-2 text-sm group"
            role="listitem"
          >
            {att.preview ? (
              <div className="h-8 w-8 shrink-0 overflow-hidden rounded-lg">
                <img
                  src={att.preview}
                  alt={`Preview of ${att.file.name}`}
                  className="h-full w-full object-cover"
                />
              </div>
            ) : (
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#374151]">
                {getFileIcon(att.file.name)}
              </div>
            )}
            <div className="flex flex-col min-w-0 max-w-[120px]">
              <span className="truncate text-xs font-medium text-foreground">
                {att.file.name}
              </span>
              <span className="text-[10px] text-muted-foreground">
                {formatFileSize(att.file.size)}
              </span>
            </div>
            <button
              onClick={() => onRemove(att.id)}
              className="ml-1 flex h-5 w-5 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-[#374151] hover:text-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[#3B82F6]"
              aria-label={`Remove ${att.file.name}`}
              type="button"
            >
              <X className="h-3 w-3" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
}

interface RecordingPreviewProps {
  audioUrl: string | null;
  duration: number;
  isPlaying: boolean;
  onPlay: () => void;
  onPause: () => void;
  onDelete: () => void;
  onSend: () => void;
}

export function RecordingPreview({
  audioUrl,
  duration,
  isPlaying,
  onPlay,
  onPause,
  onDelete,
  onSend,
}: RecordingPreviewProps) {
  const formatTime = (s: number) => {
    const mins = Math.floor(s / 60);
    const secs = s % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  if (!audioUrl) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="flex items-center gap-3 rounded-xl border border-[#2D3748] bg-[#1F2937] px-4 py-3"
    >
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={isPlaying ? onPause : onPlay}
        className="flex h-8 w-8 items-center justify-center rounded-full bg-[#3B82F6] text-white"
        aria-label={isPlaying ? "Pause recording" : "Play recording"}
        type="button"
      >
        {isPlaying ? (
          <Pause className="h-4 w-4" fill="currentColor" />
        ) : (
          <Play className="h-4 w-4 ml-0.5" fill="currentColor" />
        )}
      </motion.button>
      <span className="font-mono text-sm text-foreground">{formatTime(duration)}</span>
      <div className="flex-1" />
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onDelete}
        className="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-[#374151] hover:text-red-400"
        aria-label="Delete recording"
        type="button"
      >
        <Trash2 className="h-4 w-4" />
      </motion.button>
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={onSend}
        className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#3B82F6] text-white transition-colors hover:bg-[#2563EB]"
        aria-label="Send recording"
        type="button"
      >
        <Send className="h-4 w-4" />
      </motion.button>
    </motion.div>
  );
}
