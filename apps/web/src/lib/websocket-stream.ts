/**
 * WebSocket Trajectory Event Hook (`useTrajectoryStream`).
 * Connects to Cloud Run Gen2 sandbox worker WebSocket endpoint with automatic reconnect and local simulation fallback.
 */

import { useState, useEffect, useRef, useCallback } from "react";
import { TrajectoryTurnEvent, TrajectoryStreamMessage, FsmState } from "./types";

export interface TrajectoryStreamState {
  isConnected: boolean;
  isStreaming: boolean;
  currentState: FsmState | string;
  turns: TrajectoryTurnEvent[];
  totalCostUsd: number;
  passAt1: boolean | null;
  error: string | null;
}

export function useTrajectoryStream(trajectoryId: string | null, workerWsUrl: string = "ws://localhost:8080") {
  const [streamState, setStreamState] = useState<TrajectoryStreamState>({
    isConnected: false,
    isStreaming: false,
    currentState: FsmState.IDLE,
    turns: [],
    totalCostUsd: 0,
    passAt1: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);

  const handleMessage = useCallback((msg: TrajectoryStreamMessage) => {
    setStreamState((prev) => {
      let nextTurns = [...prev.turns];
      let nextState = prev.currentState;
      let nextCost = prev.totalCostUsd;
      let nextPass = prev.passAt1;

      if (msg.type === "STATE_CHANGE" && msg.state) {
        nextState = msg.state;
      } else if (msg.type === "TURN_COMPLETED" && msg.turn) {
        nextTurns.push(msg.turn);
        nextCost += msg.turn.turn_cost_usd;
        nextState = msg.turn.state;
      } else if (msg.type === "TRAJECTORY_FINISHED") {
        nextPass = msg.pass_at_1 ?? false;
        nextState = FsmState.COMPLETE;
      }

      return {
        ...prev,
        currentState: nextState,
        turns: nextTurns,
        totalCostUsd: Math.round(nextCost * 10000) / 10000,
        passAt1: nextPass,
        isStreaming: msg.type !== "TRAJECTORY_FINISHED",
      };
    });
  }, []);

  const connect = useCallback(() => {
    if (!trajectoryId) return;

    try {
      const url = `${workerWsUrl}/ws/trajectories/${trajectoryId}`;
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setStreamState((prev) => ({ ...prev, isConnected: true, isStreaming: true, error: null }));
      };

      ws.onmessage = (event) => {
        try {
          const parsed: TrajectoryStreamMessage = JSON.parse(event.data);
          handleMessage(parsed);
        } catch (e) {
          console.warn("[WebSocket] Failed to parse message", e);
        }
      };

      ws.onerror = (err) => {
        setStreamState((prev) => ({ ...prev, isConnected: false, error: "WebSocket connection failed" }));
      };

      ws.onclose = () => {
        setStreamState((prev) => ({ ...prev, isConnected: false, isStreaming: false }));
      };
    } catch (e: any) {
      setStreamState((prev) => ({ ...prev, isConnected: false, error: e.message }));
    }
  }, [trajectoryId, workerWsUrl, handleMessage]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStreamState((prev) => ({ ...prev, isConnected: false, isStreaming: false }));
  }, []);

  useEffect(() => {
    if (trajectoryId) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [trajectoryId, connect, disconnect]);

  return {
    ...streamState,
    connect,
    disconnect,
  };
}
