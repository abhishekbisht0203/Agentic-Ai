"use client";

import React, { useCallback } from "react";
import { motion } from "framer-motion";
import { Mic, Square } from "lucide-react";

interface MicButtonProps {
  isListening: boolean;
  isRecording: boolean;
  isSupported: boolean;
  onToggleListening: () => void;
  onToggleRecording: () => void;
  disabled?: boolean;
}

export function MicButton({
  isListening,
  isRecording,
  isSupported,
  onToggleListening,
  onToggleRecording,
  disabled = false,
}: MicButtonProps) {
  const handleClick = useCallback(() => {
    if (isListening || isRecording) {
      onToggleListening();
    } else {
      onToggleListening();
    }
  }, [isListening, isRecording, onToggleListening]);

  const handleContextMenu = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      if (!isListening && !isRecording) {
        onToggleRecording();
      }
    },
    [isListening, isRecording, onToggleRecording]
  );

  if (!isSupported) return null;

  const isActive = isListening || isRecording;

  return (
    <motion.button
      whileHover={{ scale: 1.08 }}
      whileTap={{ scale: 0.95 }}
      onClick={handleClick}
      onContextMenu={handleContextMenu}
      disabled={disabled}
      className={`relative flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3B82F6] ${
        isActive
          ? "bg-red-500/20 text-red-400"
          : "text-muted-foreground hover:bg-[#374151] hover:text-foreground"
      } disabled:opacity-40 disabled:pointer-events-none`}
      aria-label={isActive ? "Stop voice input" : "Start voice input"}
      title={isActive ? "Stop voice input" : "Voice input (click: speech-to-text, right-click: record audio)"}
      type="button"
    >
      {isActive ? (
        <Square className="h-4 w-4" fill="currentColor" />
      ) : (
        <Mic className="h-[18px] w-[18px]" />
      )}
      {isActive && (
        <motion.span
          className="absolute inset-0 rounded-xl border-2 border-red-500/50"
          animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0, 0.5] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
          aria-hidden="true"
        />
      )}
    </motion.button>
  );
}
