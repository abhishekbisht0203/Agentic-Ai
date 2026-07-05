"use client";

import { useCallback, useRef, useEffect } from "react";

interface UseAutoResizeOptions {
  minHeight?: number;
  maxHeight?: number;
}

export function useAutoResizeTextarea(options: UseAutoResizeOptions = {}) {
  const { minHeight = 60, maxHeight = 220 } = options;
  const ref = useRef<HTMLTextAreaElement>(null);

  const resize = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    const newHeight = Math.min(Math.max(el.scrollHeight, minHeight), maxHeight);
    el.style.height = `${newHeight}px`;
    el.style.overflowY = el.scrollHeight > maxHeight ? "auto" : "hidden";
  }, [minHeight, maxHeight]);

  const reset = useCallback(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = `${minHeight}px`;
    el.style.overflowY = "hidden";
  }, [minHeight]);

  useEffect(() => {
    const el = ref.current;
    if (el) {
      el.style.height = `${minHeight}px`;
    }
  }, [minHeight]);

  return { ref, resize, reset };
}
