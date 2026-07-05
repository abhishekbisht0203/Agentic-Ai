"use client";

import React from "react";

interface RecordingTimerProps {
  duration: number;
  isRecording: boolean;
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

export function RecordingTimer({ duration, isRecording }: RecordingTimerProps) {
  return (
    <div className="flex items-center gap-2 text-sm font-mono" role="timer" aria-live="polite">
      {isRecording && (
        <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" aria-hidden="true" />
      )}
      <span className={isRecording ? "text-red-400" : "text-muted-foreground"}>
        {formatTime(duration)}
      </span>
    </div>
  );
}
