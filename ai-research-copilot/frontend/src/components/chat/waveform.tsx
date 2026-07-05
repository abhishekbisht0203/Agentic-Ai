"use client";

import React, { useMemo } from "react";

interface WaveformProps {
  isRecording: boolean;
  barCount?: number;
}

export function Waveform({ isRecording, barCount = 5 }: WaveformProps) {
  const bars = useMemo(() => Array.from({ length: barCount }, (_, i) => i), [barCount]);

  return (
    <div className="flex items-center gap-[3px] h-5" aria-hidden="true">
      {bars.map((i) => (
        <div
          key={i}
          className={`w-[3px] rounded-full transition-all duration-150 ${
            isRecording ? "bg-red-500" : "bg-muted-foreground/40"
          }`}
          style={{
            animation: isRecording
              ? `waveBar 0.${4 + (i % 3)}s ease-in-out ${i * 0.08}s infinite alternate`
              : "none",
            height: isRecording ? undefined : "4px",
          }}
        />
      ))}
      <style>{`
        @keyframes waveBar {
          0% { height: 4px; }
          100% { height: 18px; }
        }
      `}</style>
    </div>
  );
}
