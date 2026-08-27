"use client";

import React, { useRef, useEffect } from "react";
import { WebRtcClientManager } from "@/lib/webrtc-client";

interface AudioWaveformCanvasProps {
  sessionManager: WebRtcClientManager | null;
  isActive: boolean;
  color?: string;
  className?: string;
}

export function AudioWaveformCanvas({
  sessionManager,
  isActive,
  color = "#00F0FF",
  className = "w-full h-24",
}: AudioWaveformCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const dataArray = new Uint8Array(64);

    const render = () => {
      animationFrameRef.current = requestAnimationFrame(render);

      const width = canvas.width;
      const height = canvas.height;

      ctx.clearRect(0, 0, width, height);

      if (isActive && sessionManager) {
        sessionManager.getFrequencyData(dataArray);
      } else {
        // Idle ambient breathing line
        dataArray.fill(12);
      }

      // Draw mirrored futuristic frequency bars
      const barCount = 36;
      const barWidth = (width / barCount) * 0.65;
      const gap = (width / barCount) * 0.35;

      for (let i = 0; i < barCount; i++) {
        const val = dataArray[i % dataArray.length] || 10;
        const normalized = Math.max(0.08, val / 255);
        const barHeight = normalized * height * 0.85;
        const x = i * (barWidth + gap) + gap / 2;
        const y = (height - barHeight) / 2;

        // Gradient glow
        const gradient = ctx.createLinearGradient(0, y, 0, y + barHeight);
        if (isActive) {
          gradient.addColorStop(0, color);
          gradient.addColorStop(0.5, "#10B981");
          gradient.addColorStop(1, color);
        } else {
          gradient.addColorStop(0, "rgba(255, 255, 255, 0.15)");
          gradient.addColorStop(1, "rgba(255, 255, 255, 0.05)");
        }

        ctx.fillStyle = gradient;
        ctx.shadowColor = isActive ? color : "transparent";
        ctx.shadowBlur = isActive ? 12 : 0;

        // Rounded bar
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barHeight, 3);
        ctx.fill();
      }
    };

    render();

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [sessionManager, isActive, color]);

  return (
    <canvas
      ref={canvasRef}
      width={480}
      height={96}
      className={`rounded-lg bg-black/40 border border-white/10 ${className}`}
    />
  );
}
