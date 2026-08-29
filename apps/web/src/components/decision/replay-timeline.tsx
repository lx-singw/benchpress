"use client";

import React, { useState } from "react";
import { GitCommit, CheckCircle2, ChevronRight, Hash, Clock, UserCheck } from "lucide-react";
import type { ReplayEvent } from "@benchpress/contracts";

interface ReplayTimelineProps {
  events: ReplayEvent[];
}

export function ReplayTimeline({ events }: ReplayTimelineProps) {
  const [selectedEvent, setSelectedEvent] = useState<ReplayEvent | null>(events[events.length - 1] || null);

  return (
    <div className="rounded-2xl bg-[#0D121F]/80 backdrop-blur-xl border border-white/10 p-6 lg:p-8">
      <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-6">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <GitCommit className="w-5 h-5 text-cyan-400" />
            Deterministic Replay Timeline & State Audit
          </h3>
          <p className="text-xs text-gray-400 mt-1">
            Immutable, ordered record of all 7 lifecycle state transitions and cryptographic hashes.
          </p>
        </div>
        <div className="text-xs font-mono text-cyan-300 bg-cyan-500/10 px-3 py-1.5 rounded-lg border border-cyan-500/20">
          {events.length} Verified Transitions
        </div>
      </div>

      {/* Horizontal / Wrapped Step Flow */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 mb-6">
        {events.map((evt) => {
          const isSelected = selectedEvent?.sequence_id === evt.sequence_id;
          return (
            <button
              key={evt.sequence_id}
              onClick={() => setSelectedEvent(evt)}
              className={`p-3 rounded-xl border text-left transition-all duration-200 ${
                isSelected
                  ? "bg-cyan-500/20 border-cyan-400 shadow-[0_0_20px_rgba(6,182,212,0.2)]"
                  : "bg-white/[0.03] border-white/10 hover:bg-white/[0.06] hover:border-white/20"
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono text-gray-500 mb-1">
                <span>STEP {evt.sequence_id}</span>
                <CheckCircle2 className={`w-3 h-3 ${isSelected ? "text-cyan-400" : "text-emerald-500"}`} />
              </div>
              <div className="text-xs font-bold text-white font-mono truncate">{evt.to_state}</div>
              <div className="text-[10px] text-gray-400 truncate mt-0.5">{evt.actor}</div>
            </button>
          );
        })}
      </div>

      {/* Selected Step Detail Panel */}
      {selectedEvent && (
        <div className="rounded-xl bg-black/50 border border-white/10 p-5 font-mono text-xs text-gray-300">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-3 mb-4">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[11px] font-bold">
                TRANSITION #{selectedEvent.sequence_id}
              </span>
              <span className="text-gray-400">{selectedEvent.from_state}</span>
              <ChevronRight className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-emerald-400 font-bold">{selectedEvent.to_state}</span>
            </div>
            <div className="flex items-center gap-1.5 text-gray-400 text-[11px]">
              <Clock className="w-3.5 h-3.5 text-gray-500" />
              {selectedEvent.timestamp}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="md:col-span-2 space-y-2">
              <div className="text-gray-400">Transition Rationale:</div>
              <div className="p-3 rounded-lg bg-white/[0.03] border border-white/5 text-gray-200 font-sans text-xs leading-relaxed">
                {selectedEvent.transition_reason}
              </div>
            </div>

            <div className="space-y-3 bg-white/[0.02] p-3 rounded-lg border border-white/5">
              <div>
                <div className="text-gray-500 text-[10px] uppercase">Executing Actor</div>
                <div className="text-cyan-300 font-semibold flex items-center gap-1.5 mt-0.5">
                  <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
                  {selectedEvent.actor}
                </div>
              </div>

              <div>
                <div className="text-gray-500 text-[10px] uppercase">Payload SHA-256 Digest</div>
                <div className="text-gray-400 font-mono text-[10px] break-all flex items-center gap-1 mt-0.5">
                  <Hash className="w-3 h-3 text-gray-500 shrink-0" />
                  {selectedEvent.payload_hash}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
