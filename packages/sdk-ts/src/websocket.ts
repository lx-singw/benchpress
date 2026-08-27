/**
 * Live Trajectory WebSocket Stream Client.
 */

export interface TrajectoryStreamListener {
  onStateChange?: (state: string) => void;
  onTurnCompleted?: (turn: any) => void;
  onFinished?: (status: string, passAt1: boolean) => void;
  onError?: (error: any) => void;
}

export class TrajectoryStreamClient {
  private ws: WebSocket | null = null;
  private isClosed: boolean = false;

  constructor(
    private readonly trajectoryId: string,
    private readonly wsUrl: string = "ws://localhost:8080"
  ) {}

  public subscribe(listeners: TrajectoryStreamListener): () => void {
    const url = `${this.wsUrl}/ws/trajectories/${this.trajectoryId}`;
    try {
      this.ws = new WebSocket(url);

      this.ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === "STATE_CHANGE") {
            listeners.onStateChange?.(msg.state);
          } else if (msg.type === "TURN_COMPLETED") {
            listeners.onTurnCompleted?.(msg.turn);
          } else if (msg.type === "TRAJECTORY_FINISHED") {
            listeners.onFinished?.(msg.status, msg.pass_at_1);
          }
        } catch (e) {
          listeners.onError?.(e);
        }
      };

      this.ws.onerror = (err) => {
        listeners.onError?.(err);
      };
    } catch (e) {
      listeners.onError?.(e);
    }

    return () => {
      this.isClosed = true;
      if (this.ws) {
        this.ws.close();
        this.ws = null;
      }
    };
  }
}
