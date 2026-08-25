import React from "react";
import { Cpu, ShieldCheck, Zap } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full border-t border-white/10 bg-[#0A0D14] py-8 text-xs text-gray-400">
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 sm:flex-row sm:px-6 lg:px-8">
        <div className="flex items-center gap-2">
          <Cpu className="h-4 w-4 text-[#00F0FF]" />
          <span className="font-mono text-gray-200">Benchpress Engine</span>
          <span>•</span>
          <span>Google Cloud Hackathon 2026</span>
        </div>

        <div className="flex items-center gap-6">
          <div className="flex items-center gap-1.5 text-gray-400">
            <ShieldCheck className="h-3.5 w-3.5 text-[#10B981]" />
            <span>gVisor Isolated Worker Fleet</span>
          </div>
          <div className="flex items-center gap-1.5 text-gray-400">
            <Zap className="h-3.5 w-3.5 text-[#F59E0B]" />
            <span>BigQuery Write Streamer</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
