"use client";

import React from "react";
import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

const suggestions = [
  "Explain quantum computing in simple terms",
  "Compare transformer and RNN architectures",
  "What are the latest breakthroughs in AI?",
  "Help me analyze this research paper",
];

interface SuggestionChipsProps {
  onSelect: (text: string) => void;
  disabled?: boolean;
}

export function SuggestionChips({ onSelect, disabled = false }: SuggestionChipsProps) {
  return (
    <div className="grid w-full max-w-2xl gap-3 sm:grid-cols-2" role="group" aria-label="Suggested prompts">
      {suggestions.map((suggestion, i) => (
        <motion.button
          key={suggestion}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.08, type: "spring", stiffness: 300, damping: 25 }}
          whileHover={{ scale: 1.02, y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onSelect(suggestion)}
          disabled={disabled}
          className="flex items-start gap-3 rounded-xl border border-[#2D3748] bg-[#1F2937]/50 p-4 text-left text-sm transition-colors hover:border-[#3B82F6]/30 hover:bg-[#1F2937] disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3B82F6]"
          type="button"
        >
          <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-[#3B82F6]" />
          <span className="text-muted-foreground">{suggestion}</span>
        </motion.button>
      ))}
    </div>
  );
}
