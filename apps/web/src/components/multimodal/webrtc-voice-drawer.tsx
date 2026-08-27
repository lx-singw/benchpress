"use client";

import React, { useState, useEffect, useRef } from "react";
import { Mic, MicOff, X, Radio, Volume2, Sparkles, Send, MessageSquare } from "lucide-react";
import { WebRtcClientManager, VoiceMessage } from "@/lib/webrtc-client";
import { AudioWaveformCanvas } from "./audio-waveform-canvas";

interface WebRtcVoiceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function WebRtcVoiceDrawer({ isOpen, onClose }: WebRtcVoiceDrawerProps) {
  const [sessionManager, setSessionManager] = useState<WebRtcClientManager | null>(null);
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [status, setStatus] = useState<"idle" | "listening" | "thinking" | "speaking">("idle");
  const [inputText, setInputText] = useState("");
  const [isMicBlocked, setIsMicBlocked] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Initialize WebRTC session manager
  useEffect(() => {
    const mgr = new WebRtcClientManager();
    mgr.setCallbacks(
      (msg) => setMessages((prev) => [...prev, msg]),
      (st) => setStatus(st),
      (blocked) => setIsMicBlocked(blocked)
    );
    setSessionManager(mgr);

    return () => {
      mgr.disconnect();
    };
  }, []);

  // Connect / Disconnect on drawer open
  useEffect(() => {
    if (isOpen && sessionManager) {
      sessionManager.connect();
    } else if (!isOpen && sessionManager) {
      sessionManager.disconnect();
    }
  }, [isOpen, sessionManager]);

  // Auto-scroll messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Global Keyboard Toggle (Spacebar or 'V')
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.key === "v" || e.key === "V") && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement)?.tagName)) {
        e.preventDefault();
        if (isOpen) onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  const handleSend = () => {
    if (!inputText.trim() || !sessionManager) return;
    sessionManager.sendUserQuery(inputText);
    setInputText("");
  };

  const handleQuickPrompt = (prompt: string) => {
    if (!sessionManager) return;
    sessionManager.sendUserQuery(prompt);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-obsidian-900/95 border-l border-white/10 shadow-2xl backdrop-blur-2xl flex flex-col animate-in slide-in-from-right duration-300">
      {/* Drawer Header */}
      <div className="flex items-center justify-between p-5 border-b border-white/10">
        <div className="flex items-center gap-2.5">
          <div className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00F0FF] opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-[#00F0FF]" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm tracking-tight flex items-center gap-1.5">
              Gemini Live Voice Copilot <Sparkles className="w-3.5 h-3.5 text-amber-400" />
            </h3>
            <span className="text-[11px] font-mono text-zinc-400">Vertex AI WebRTC Duplex (&lt;200ms)</span>
          </div>
        </div>

        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-white/10 transition"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Non-Blocking Microphone Graceful Degradation Banner */}
      {isMicBlocked && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2.5 flex items-center gap-2 text-xs font-mono text-amber-300 animate-in fade-in duration-300">
          <MicOff className="w-4 h-4 text-amber-400 shrink-0" />
          <span>Microphone access blocked — Switched to Interactive Voice Simulator Mode</span>
        </div>
      )}

      {/* Waveform Oscilloscope & Status Banner */}
      <div className="p-5 bg-white/[0.02] border-b border-white/5 space-y-3">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-zinc-400">AudioWorklet Frequency:</span>
          <span
            className={`font-bold px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider ${
              status === "speaking"
                ? "bg-[#00F0FF]/20 text-[#00F0FF]"
                : status === "listening"
                ? "bg-emerald-500/20 text-emerald-300 animate-pulse"
                : "bg-amber-500/20 text-amber-300"
            }`}
          >
            {isMicBlocked ? "SIMULATOR ACTIVE" : status}
          </span>
        </div>

        <AudioWaveformCanvas sessionManager={sessionManager} isActive={isOpen} color="#00F0FF" />

        {/* 3 Clickable Spoken Judge Diagnostic Prompts */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">Judge Voice Prompts:</span>
          <div className="flex flex-col gap-1.5">
            {[
              { label: "💬 Why did turn 12 fail on regex validation?", query: "Why did turn 12 fail on regex validation?" },
              { label: "💬 Explain how the hybrid routing saved 87% cost on this run.", query: "Explain how the hybrid routing saved 87% cost on this run." },
              { label: "💬 What tool did the AST Healer patch in turn 4?", query: "What tool did the AST Healer patch in turn 4?" },
            ].map((item) => (
              <button
                key={item.query}
                onClick={() => handleQuickPrompt(item.query)}
                className="text-[11px] font-mono text-left px-3 py-1.5 rounded-md bg-white/5 hover:bg-[#00F0FF]/15 border border-white/10 text-zinc-300 hover:text-[#00F0FF] transition shadow-sm"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Conversation Thread */}
      <div className="flex-1 overflow-y-auto p-5 space-y-3.5">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex flex-col ${msg.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div className="flex items-center gap-1.5 text-[10px] font-mono text-zinc-500 mb-1">
              {msg.sender === "user" ? (
                <>
                  <span>You</span>
                  <Mic className="w-3 h-3 text-emerald-400" />
                </>
              ) : (
                <>
                  <Volume2 className="w-3 h-3 text-[#00F0FF]" />
                  <span>Gemini Live</span>
                </>
              )}
              <span>• {msg.timestamp}</span>
            </div>

            <div
              className={`max-w-[85%] rounded-xl p-3 text-xs leading-relaxed ${
                msg.sender === "user"
                  ? "bg-emerald-500/20 text-emerald-100 border border-emerald-500/30"
                  : "bg-white/5 text-zinc-200 border border-white/10 shadow-lg"
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-white/10 bg-black/40 flex items-center gap-2">
        <input
          type="text"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Ask spoken diagnostic question..."
          className="flex-1 rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-xs font-sans text-white placeholder-zinc-500 focus:border-[#00F0FF] focus:outline-none"
        />
        <button
          onClick={handleSend}
          className="p-2 rounded-lg bg-[#00F0FF] text-[#0A0D14] hover:opacity-90 transition"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
