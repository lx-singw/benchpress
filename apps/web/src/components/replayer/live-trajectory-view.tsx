"use client";

import React, { useState } from "react";
import { SandboxTerminalPane } from "./sandbox-terminal-pane";
import { TokenWaterfallChart } from "../charts/token-waterfall-chart";
import { TrajectoryTurnEvent } from "@/lib/types";

interface LiveTrajectoryViewProps {
  turns: TrajectoryTurnEvent[];
  selectedTurnIndex?: number;
}

export function LiveTrajectoryView({ turns, selectedTurnIndex }: LiveTrajectoryViewProps) {
  const [activeTurnIdx, setActiveTurnIdx] = useState<number | null>(null);

  const currentTurn = activeTurnIdx !== null
    ? turns.find((t) => t.turn_index === activeTurnIdx)
    : turns.length > 0
    ? turns[turns.length - 1]
    : null;

  return (
    <div className="space-y-6">
      {/* Split-View Grid: Virtual Terminal (Left) vs Token Burn Waterfall (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <SandboxTerminalPane currentTurn={currentTurn} />
        </div>
        <div className="lg:col-span-5">
          <TokenWaterfallChart turns={turns} />
        </div>
      </div>
    </div>
  );
}
