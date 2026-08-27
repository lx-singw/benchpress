"use client";

import React from "react";
import { Mic, Volume2 } from "lucide-react";

interface LiveCaptionsOverlayProps {
  latestText?: string;
  sender?: "user" | "gemini";
  isVisible: boolean;
}

export function LiveCaptionsOverlay({ latestText, sender = "gemini", isVisible }: LiveCaptionsOverlayProps) {
  if (!isVisible || !latestText) return null;

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50 max-w-xl w-full px-4 animate-in fade-in slide-in-from-bottom-2">
      <div className="rounded-xl border border-[#00F0FF]/30 bg-obsidian-900/90 p-4 shadow-glass-cyan backdrop-blur-2xl text-center">
        <div className="flex items-center justify-center gap-2 mb-1.5 text-xs font-mono">
          {sender === "gemini" ? (
            <>
              <Volume2 className="w-3.5 h-3.5 text-[#00F0FF] animate-pulse" />
              <span className="text-[#00F0FF] font-semibold">Gemini Multimodal Live</span>
            </>
          ) : (
            <>
              <Mic className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-semibold">Developer Speech</span>
            </>
          )}
        </div>
        <p className="text-sm text-zinc-100 font-sans leading-relaxed">{latestText}</p>
      </div>
    </div>
  );
}
