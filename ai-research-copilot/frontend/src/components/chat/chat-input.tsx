"use client";

import React, { useState, useCallback, useEffect, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { toast } from "sonner";
import { useAutoResizeTextarea } from "@/hooks/use-auto-resize-textarea";
import { useSpeechRecognition } from "@/hooks/use-speech-recognition";
import { useVoiceRecorder } from "@/hooks/use-voice-recorder";
import { AttachmentButton } from "./attachment-button";
import { MicButton } from "./mic-button";
import { SendButton } from "./send-button";
import { Waveform } from "./waveform";
import { RecordingTimer } from "./recording-timer";
import { AttachmentPreview, RecordingPreview } from "./attachment-preview";

interface AttachmentItem {
  id: string;
  file: File;
  preview?: string;
  uploaded?: boolean;
}

interface ChatInputProps {
  onSend: (message: string, attachments?: File[]) => void;
  isLoading?: boolean;
  disabled?: boolean;
  onStop?: () => void;
  conversationId?: string;
}

export function ChatInput({ onSend, isLoading = false, disabled = false, onStop, conversationId }: ChatInputProps) {
  const [message, setMessage] = useState("");
  const [attachments, setAttachments] = useState<AttachmentItem[]>([]);
  const [showRecordingPreview, setShowRecordingPreview] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);
  const composerRef = useRef<HTMLDivElement>(null);

  const { ref: textareaRef, resize, reset } = useAutoResizeTextarea({
    minHeight: 60,
    maxHeight: 220,
  });

  const speech = useSpeechRecognition({ continuous: true, interimResults: true });
  const recorder = useVoiceRecorder();

  // Sync speech transcript to message
  useEffect(() => {
    if (speech.transcript) {
      setMessage((prev) => {
        const trimmed = prev.trimEnd();
        return trimmed ? `${trimmed} ${speech.transcript}` : speech.transcript;
      });
    }
  }, [speech.transcript]);

  // Show recording preview when recording stops with audio
  useEffect(() => {
    if (!recorder.isRecording && recorder.audioBlob && recorder.duration > 0) {
      setShowRecordingPreview(true);
    }
  }, [recorder.isRecording, recorder.audioBlob, recorder.duration]);

  // Auto-resize textarea when message changes
  useEffect(() => {
    resize();
  }, [message, resize]);

  // Upload attachments to backend and send message
  const handleSend = useCallback(async () => {
    const trimmed = message.trim();
    if (!trimmed || isLoading || disabled) return;

    // Pass files to parent for upload (parent handles conversation creation first)
    const files = attachments.length > 0 ? attachments.map(a => a.file) : undefined;

    onSend(trimmed, files);
    setMessage("");
    setAttachments([]);
    reset();
    speech.resetTranscript();
  }, [message, isLoading, disabled, onSend, reset, speech, attachments]);

  // Handle stopping generation
  const handleStop = useCallback(() => {
    onStop?.();
  }, [onStop]);

  // Handle file selections
  const handleFilesSelected = useCallback((files: File[]) => {
    const newAttachments: AttachmentItem[] = files.map((file) => {
      const id = `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
      const isImage = file.type.startsWith("image/");
      return {
        id,
        file,
        preview: isImage ? URL.createObjectURL(file) : undefined,
      };
    });
    setAttachments((prev) => [...prev, ...newAttachments]);
  }, []);

  // Remove attachment
  const handleRemoveAttachment = useCallback((id: string) => {
    setAttachments((prev) => {
      const att = prev.find((a) => a.id === id);
      if (att?.preview) URL.revokeObjectURL(att.preview);
      return prev.filter((a) => a.id !== id);
    });
  }, []);

  // Toggle speech recognition
  const handleToggleListening = useCallback(() => {
    if (speech.isListening) {
      speech.stop();
    } else {
      recorder.cancel();
      setShowRecordingPreview(false);
      speech.start();
      toast.info("Voice input active — speak now");
    }
  }, [speech, recorder]);

  // Toggle audio recording
  const handleToggleRecording = useCallback(async () => {
    if (recorder.isRecording) {
      recorder.stop();
    } else {
      speech.stop();
      speech.resetTranscript();
      try {
        await recorder.start();
      } catch {
        toast.error("Could not start recording");
      }
    }
  }, [recorder, speech]);

  // Send recording as text (transcribed)
  const handleSendRecording = useCallback(() => {
    if (message.trim()) {
      handleSend();
    }
    setShowRecordingPreview(false);
    recorder.deleteRecording();
  }, [message, handleSend, recorder]);

  // Delete recording
  const handleDeleteRecording = useCallback(() => {
    setShowRecordingPreview(false);
    recorder.deleteRecording();
  }, [recorder]);

  // Keyboard shortcuts
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
      if (e.key === "Escape") {
        if (speech.isListening) {
          speech.stop();
          toast.info("Voice input stopped");
        }
        if (recorder.isRecording) {
          recorder.cancel();
          setShowRecordingPreview(false);
          toast.info("Recording cancelled");
        }
      }
    },
    [handleSend, speech, recorder]
  );

  // Handle paste (images)
  const handlePaste = useCallback(
    (e: React.ClipboardEvent<HTMLTextAreaElement>) => {
      const items = Array.from(e.clipboardData.items);
      const imageItems = items.filter((item) => item.type.startsWith("image/"));
      if (imageItems.length > 0) {
        e.preventDefault();
        const files = imageItems
          .map((item) => item.getAsFile())
          .filter((f): f is File => f !== null);
        handleFilesSelected(files);
      }
    },
    [handleFilesSelected]
  );

  // Drag & Drop
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (composerRef.current && !composerRef.current.contains(e.relatedTarget as Node)) {
      setIsDragOver(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsDragOver(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        handleFilesSelected(files);
      }
    },
    [handleFilesSelected]
  );

  // Ctrl+K focus shortcut
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        textareaRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleGlobalKeyDown);
    return () => window.removeEventListener("keydown", handleGlobalKeyDown);
  }, [textareaRef]);

  // Cleanup attachment previews on unmount
  useEffect(() => {
    return () => {
      attachments.forEach((att) => {
        if (att.preview) URL.revokeObjectURL(att.preview);
      });
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const canSend = Boolean(message.trim()) && !isLoading && !disabled;
  const isGenerating = isLoading && !disabled;

  const displayText = useMemo(() => {
    if (speech.interimTranscript) {
      const trimmed = message.trimEnd();
      return trimmed ? `${trimmed} ${speech.interimTranscript}` : speech.interimTranscript;
    }
    return message;
  }, [message, speech.interimTranscript]);

  return (
    <div
      ref={composerRef}
      className="border-t border-[#2D3748] bg-[#111827] px-4 py-4 sm:px-6"
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      role="form"
      aria-label="Chat message composer"
    >
      <div className="mx-auto max-w-3xl space-y-3">
        {/* Attachment previews */}
        <AnimatePresence>
          {attachments.length > 0 && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              <AttachmentPreview
                attachments={attachments}
                onRemove={handleRemoveAttachment}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Recording preview */}
        <AnimatePresence>
          {showRecordingPreview && recorder.audioUrl && (
            <RecordingPreview
              audioUrl={recorder.audioUrl}
              duration={recorder.duration}
              isPlaying={recorder.isPlaying}
              onPlay={recorder.play}
              onPause={recorder.pause}
              onDelete={handleDeleteRecording}
              onSend={handleSendRecording}
            />
          )}
        </AnimatePresence>

        {/* Main composer area */}
        <motion.div
          animate={{
            borderColor: isDragOver ? "#3B82F6" : speech.isListening || recorder.isRecording ? "#EF444440" : "#2D3748",
          }}
          className={`relative flex items-end gap-2 rounded-2xl border bg-[#1F2937] p-2 transition-shadow ${
            isDragOver
              ? "ring-2 ring-[#3B82F6]/50 shadow-lg shadow-[#3B82F6]/10"
              : speech.isListening || recorder.isRecording
              ? "ring-1 ring-red-500/20"
              : "focus-within:ring-1 focus-within:ring-[#3B82F6]/30"
          }`}
        >
          {/* Drag overlay */}
          <AnimatePresence>
            {isDragOver && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl border-2 border-dashed border-[#3B82F6] bg-[#111827]/90 backdrop-blur-sm"
              >
                <span className="text-sm font-medium text-[#3B82F6]">
                  Drop files here
                </span>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Left: Attachment button */}
          <div className="flex items-end pb-0.5">
            <AttachmentButton
              onFilesSelected={handleFilesSelected}
              disabled={disabled || isLoading}
            />
          </div>

          {/* Center: Textarea */}
          <div className="flex-1 min-w-0">
            {/* Active voice indicators */}
            <AnimatePresence>
              {(speech.isListening || recorder.isRecording) && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-2 pb-2"
                >
                  {recorder.isRecording && (
                    <>
                      <Waveform isRecording={true} />
                      <RecordingTimer
                        duration={recorder.duration}
                        isRecording={true}
                      />
                    </>
                  )}
                  {speech.isListening && (
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                      <span className="text-xs text-red-400">Listening...</span>
                      <Waveform isRecording={true} barCount={3} />
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            <textarea
              ref={textareaRef}
              value={displayText}
              onChange={(e) => {
                setMessage(e.target.value);
                if (speech.isListening) {
                  speech.stop();
                  speech.resetTranscript();
                }
              }}
              onKeyDown={handleKeyDown}
              onPaste={handlePaste}
              placeholder={
                speech.isListening
                  ? "Listening..."
                  : recorder.isRecording
                  ? "Recording audio..."
                  : "Ask anything..."
              }
              disabled={disabled}
              rows={1}
              className="w-full resize-none border-0 bg-transparent px-1 py-1.5 text-sm text-foreground placeholder:text-[#6B7280] focus-visible:outline-none focus-visible:ring-0 disabled:cursor-not-allowed disabled:opacity-50"
              style={{ minHeight: "60px", maxHeight: "220px" }}
              aria-label="Message input"
              aria-describedby="chat-input-hint"
            />
          </div>

          {/* Right: Mic + Send */}
          <div className="flex items-end gap-1.5 pb-0.5">
            <MicButton
              isListening={speech.isListening}
              isRecording={recorder.isRecording}
              isSupported={speech.isSupported}
              onToggleListening={handleToggleListening}
              onToggleRecording={handleToggleRecording}
              disabled={disabled}
            />
            <SendButton
              canSend={canSend}
              isGenerating={isGenerating}
              isLoading={isLoading}
              onSend={handleSend}
              onStop={handleStop}
            />
          </div>
        </motion.div>

        {/* Footer hint */}
        <p
          id="chat-input-hint"
          className="text-center text-xs text-[#6B7280]"
        >
          <kbd className="mx-0.5 rounded border border-[#2D3748] bg-[#1F2937] px-1.5 py-0.5 text-[10px] font-mono text-[#9CA3AF]">
            Enter
          </kbd>{" "}
          to send
          <span className="mx-1.5 text-[#374151]">|</span>
          <kbd className="mx-0.5 rounded border border-[#2D3748] bg-[#1F2937] px-1.5 py-0.5 text-[10px] font-mono text-[#9CA3AF]">
            Shift+Enter
          </kbd>{" "}
          for new line
          <span className="mx-1.5 text-[#374151]">|</span>
          <kbd className="mx-0.5 rounded border border-[#2D3748] bg-[#1F2937] px-1.5 py-0.5 text-[10px] font-mono text-[#9CA3AF]">
            Ctrl+K
          </kbd>{" "}
          to focus
        </p>
      </div>
    </div>
  );
}
