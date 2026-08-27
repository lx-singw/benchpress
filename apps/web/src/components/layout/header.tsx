"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { Activity, Cpu, Layers, Sparkles, Terminal, Mic, Radio } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { WebRtcVoiceDrawer } from "@/components/webrtc-voice-drawer";

export function Header() {
  const [isVoiceOpen, setIsVoiceOpen] = useState(false);

  // Keyboard shortcut listener ('v' to toggle voice)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.key === "v" || e.key === "V") && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        setIsVoiceOpen((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-white/10 bg-[#0A0D14]/80 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
          {/* Brand */}
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-3 group">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-[#00F0FF]/20 to-[#10B981]/20 border border-[#00F0FF]/40 text-[#00F0FF] group-hover:shadow-glass-cyan transition-all">
                <Cpu className="h-5 w-5" />
              </div>
              <div className="flex flex-col">
                <span className="font-mono text-base font-bold tracking-wider text-white">
                  BENCH<span className="text-[#00F0FF]">PRESS</span>
                </span>
                <span className="text-[10px] uppercase tracking-widest text-gray-400">
                  Agent FinOps & Routing
                </span>
              </div>
            </Link>

            {/* Navigation Links */}
            <nav className="hidden md:flex items-center gap-1">
              <Link
                href="/"
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-300 hover:bg-white/5 hover:text-white transition-colors"
              >
                <Layers className="h-4 w-4 text-[#00F0FF]" />
                Leaderboard & Pareto
              </Link>
              <Link
                href="/live"
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-300 hover:bg-white/5 hover:text-white transition-colors"
              >
                <Activity className="h-4 w-4 text-[#10B981]" />
                Live Runner
              </Link>
              <a
                href="https://github.com"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-gray-300 hover:bg-white/5 hover:text-white transition-colors"
              >
                <Terminal className="h-4 w-4 text-purple-400" />
                SDK Docs
              </a>
            </nav>
          </div>

          {/* Right Action: Voice Copilot + Status */}
          <div className="flex items-center gap-3">
            {/* Live WebRTC Voice Copilot Button */}
            <button
              onClick={() => setIsVoiceOpen(true)}
              className="flex items-center gap-2 rounded-lg border border-[#00F0FF]/30 bg-[#00F0FF]/10 px-3 py-1.5 text-xs font-mono text-[#00F0FF] hover:bg-[#00F0FF]/20 hover:shadow-glass-cyan transition-all"
            >
              <Radio className="h-3.5 w-3.5 animate-pulse text-[#00F0FF]" />
              <span>Voice Copilot</span>
              <kbd className="hidden sm:inline-block rounded bg-[#0A0D14] px-1.5 py-0.5 text-[10px] text-gray-400">
                V
              </kbd>
            </button>

            <Badge variant="cyan" dot size="sm">
              Cloud Run Gen2
            </Badge>
          </div>
        </div>
      </header>

      {/* Slide-over WebRTC Voice Drawer */}
      <WebRtcVoiceDrawer
        isOpen={isVoiceOpen}
        onClose={() => setIsVoiceOpen(false)}
      />
    </>
  );
}
