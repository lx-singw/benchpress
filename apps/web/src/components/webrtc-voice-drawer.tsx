"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Mic,
  MicOff,
  Volume2,
  X,
  Sparkles,
  Send,
  Zap,
  Radio,
  Layers,
  CheckCircle2,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { GlassCard } from "@/components/ui/glass-card";
import { getWebRtcSession, WebRtcStatus } from "@/lib/webrtc-session";

interface TranscriptMessage {
  id: string;
  speaker: "user" | "agent";
  text: string;
  timestamp: string;
}

interface WebRtcVoiceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

export function WebRtcVoiceDrawer({ isOpen, onClose }: WebRtcVoiceDrawerProps) {
  const [status, setStatus] = useState<WebRtcStatus>("DISCONNECTED");
  const [transcripts, setTranscripts] = useState<TranscriptMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const sessionRef = useRef(getWebRtcSession());
  const chatScrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const session = sessionRef.current;

    session.onStatusChange((newStatus) => {
      setStatus(newStatus);
    });

    session.onTranscript((speaker, text) => {
      setTranscripts((prev) => [
        ...prev,
        {
          id: `${Date.now()}-${Math.random()}`,
          speaker,
          text,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
        },
      ]);
    });

    if (isOpen && status === "DISCONNECTED") {
      session.connect();
    }
  }, [isOpen, status]);

  // Auto-scroll chat transcript
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [transcripts]);

  // Audio Waveform Animation Loop
  useEffect(() => {
    if (!isOpen) return;

    let animationFrameId: number;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const session = sessionRef.current;
    const bufferLength = 32;
    const dataArray = new Uint8Array(bufferLength);

    const render = () => {
      session.getAudioFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 1.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.9;

        // Gradient neon color: Cyan to Emerald
        const gradient = ctx.createLinearGradient(0, canvas.height, 0, 0);
        gradient.addColorStop(0, "rgba(0, 240, 255, 0.4)");
        gradient.addColorStop(0.5, "#00F0FF");
        gradient.addColorStop(1, "#10B981");

        ctx.fillStyle = gradient;
        ctx.shadowBlur = status === "SPEAKING" ? 12 : 4;
        ctx.shadowColor = "#00F0FF";

        const y = (canvas.height - barHeight) / 2;
        ctx.fillRect(x, y, barWidth - 2, Math.max(4, barHeight));

        x += barWidth + 1;
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [isOpen, status]);

  if (!isOpen) return null;

  const handleSend = (textToSend?: string) => {
    const message = textToSend || inputText;
    if (!message.trim()) return;
    sessionRef.current.sendVoiceQuery(message);
    setInputText("");
  };

  const getStatusBadge = () => {
    switch (status) {
      case "SPEAKING":
        return <Badge variant="cyan" dot>Speaking (&lt;200ms)</Badge>;
      case "LISTENING":
        return <Badge variant="emerald" dot>Listening</Badge>;
      case "THINKING":
        return <Badge variant="amber" dot>Synthesizing...</Badge>;
      case "CONNECTING":
        return <Badge variant="neutral" dot>Establishing WebRTC...</Badge>;
      default:
        return <Badge variant="neutral">Offline</Badge>;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm transition-opacity animate-in fade-in">
      <div className="flex h-full w-full max-w-md flex-col border-l border-white/10 bg-[#0A0D14] shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 p-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#00F0FF]/10 text-[#00F0FF] border border-[#00F0FF]/30">
              <Radio className="h-4 w-4 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-white">Voice Copilot</span>
                <span className="text-[10px] text-gray-400 font-mono">Vertex Live</span>
              </div>
              <div className="mt-0.5">{getStatusBadge()}</div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-white/10 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Audio Waveform Canvas Banner */}
        <div className="border-b border-white/10 bg-[#121722]/80 p-4">
          <div className="flex items-center justify-between text-xs text-gray-400 font-mono mb-2">
            <span>Audio Worklet Visualizer</span>
            <span className="text-[#00F0FF]">48kHz PCM Duplex</span>
          </div>
          <canvas
            ref={canvasRef}
            width={380}
            height={60}
            className="w-full rounded-lg bg-[#0A0D14] border border-white/5"
          />
        </div>

        {/* Chat / Dialogue Transcript Stream */}
        <div
          ref={chatScrollRef}
          className="flex-1 overflow-y-auto p-4 space-y-4 text-xs font-sans"
        >
          {transcripts.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${msg.speaker === "user" ? "items-end" : "items-start"}`}
            >
              <div className="flex items-center gap-1.5 mb-1 font-mono text-[10px] text-gray-400">
                <span>{msg.speaker === "user" ? "You" : "Benchpress Copilot"}</span>
                <span>•</span>
                <span>{msg.timestamp}</span>
              </div>
              <div
                className={`max-w-[85%] rounded-xl p-3 leading-relaxed ${
                  msg.speaker === "user"
                    ? "bg-[#00F0FF]/20 text-white border border-[#00F0FF]/30 font-medium"
                    : "bg-[#121722] text-gray-200 border border-white/10 shadow-md"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}
        </div>

        {/* Quick Voice Queries Pills */}
        <div className="border-t border-white/10 bg-[#121722]/50 p-3">
          <div className="text-[11px] font-mono text-gray-400 mb-2 flex items-center gap-1">
            <Zap className="h-3 w-3 text-[#F59E0B]" />
            <span>Spoken Diagnostic Shortcuts:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => handleSend("Why did turn 12 fail on regex validation?")}
              className="rounded-full border border-white/10 bg-[#0A0D14] px-2.5 py-1 text-[11px] text-gray-300 hover:border-[#00F0FF] hover:text-[#00F0FF] transition-all"
            >
              🔍 Why did turn 12 fail?
            </button>
            <button
              onClick={() => handleSend("Simulate 65% token cost reduction")}
              className="rounded-full border border-white/10 bg-[#0A0D14] px-2.5 py-1 text-[11px] text-gray-300 hover:border-[#10B981] hover:text-[#10B981] transition-all"
            >
              💰 Simulate 65% cost reduction
            </button>
            <button
              onClick={() => handleSend("Analyze AST healing on Django-11099")}
              className="rounded-full border border-white/10 bg-[#0A0D14] px-2.5 py-1 text-[11px] text-gray-300 hover:border-purple-400 hover:text-purple-300 transition-all"
            >
              🛠️ Analyze AST healing
            </button>
          </div>
        </div>

        {/* Bottom Input Box */}
        <div className="border-t border-white/10 p-3 bg-[#0A0D14]">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="Speak or type a trajectory query..."
              className="flex-1 rounded-lg border border-white/10 bg-[#121722] px-3 py-2 text-xs font-mono text-white focus:border-[#00F0FF] focus:outline-none"
            />
            <button
              type="submit"
              className="rounded-lg bg-[#00F0FF] p-2 text-[#0A0D14] hover:bg-[#00F0FF]/90 transition-colors"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
