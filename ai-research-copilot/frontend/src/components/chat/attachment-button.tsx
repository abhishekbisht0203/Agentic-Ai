"use client";

import React, { useCallback, useRef } from "react";
import { Paperclip } from "lucide-react";
import { motion } from "framer-motion";

interface AttachmentButtonProps {
  onFilesSelected: (files: File[]) => void;
  disabled?: boolean;
  accept?: string;
}

export function AttachmentButton({
  onFilesSelected,
  disabled = false,
  accept = "image/*,.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.md,.zip",
}: AttachmentButtonProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  const handleClick = useCallback(() => {
    inputRef.current?.click();
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        onFilesSelected(Array.from(files));
      }
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    },
    [onFilesSelected]
  );

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={accept}
        className="hidden"
        onChange={handleChange}
        aria-hidden="true"
        tabIndex={-1}
      />
      <motion.button
        whileHover={{ scale: 1.08 }}
        whileTap={{ scale: 0.95 }}
        onClick={handleClick}
        disabled={disabled}
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-[#374151] hover:text-foreground disabled:opacity-40 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#3B82F6]"
        aria-label="Attach files"
        title="Attach files"
        type="button"
      >
        <Paperclip className="h-[18px] w-[18px]" />
      </motion.button>
    </>
  );
}
