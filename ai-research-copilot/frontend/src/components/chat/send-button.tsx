"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowUp, Square } from "lucide-react";

interface SendButtonProps {
  canSend: boolean;
  isGenerating: boolean;
  isLoading: boolean;
  onSend: () => void;
  onStop?: () => void;
}

export function SendButton({
  canSend,
  isGenerating,
  isLoading,
  onSend,
  onStop,
}: SendButtonProps) {
  if (isGenerating || isLoading) {
    return (
      <motion.button
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.92 }}
        onClick={onStop}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-[#EF4444] text-white transition-colors hover:bg-[#DC2626] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#EF4444]"
        aria-label="Stop generating"
        title="Stop generating"
        type="button"
      >
        <Square className="h-4 w-4" fill="currentColor" />
      </motion.button>
    );
  }

  return (
    <motion.button
      whileHover={canSend ? { scale: 1.08 } : {}}
      whileTap={canSend ? { scale: 0.92 } : {}}
      onClick={onSend}
      disabled={!canSend}
      className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3B82F6] ${
        canSend
          ? "bg-[#3B82F6] text-white shadow-lg shadow-[#3B82F6]/25 hover:bg-[#2563EB]"
          : "bg-[#374151] text-[#6B7280] cursor-not-allowed"
      }`}
      aria-label="Send message"
      title="Send message (Enter)"
      type="button"
    >
      <ArrowUp className="h-5 w-5" strokeWidth={2.5} />
    </motion.button>
  );
}
