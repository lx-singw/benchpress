/**
 * @benchpress/web - Cloud Tasks Dispatcher for Evaluation Orchestrator
 */

import { CloudTasksClient } from "@google-cloud/tasks";

export interface OrchestrateMessage {
  eventId: string;
  correlationId: string;
  segmentId?: string;
}

export interface IOrchestratorDispatcher {
  dispatchOrchestration(message: OrchestrateMessage): Promise<{ taskId: string; queueName: string }>;
}

class GcpOrchestratorDispatcher implements IOrchestratorDispatcher {
  private client: CloudTasksClient | null = null;
  private queuePath: string = "";
  private workerUrl: string;

  constructor() {
    this.workerUrl = (process.env.SANDBOX_WORKER_URL || "http://localhost:8000").replace(/\/$/, "");
    try {
      this.client = new CloudTasksClient();
      const project = process.env.GOOGLE_CLOUD_PROJECT || "benchpress-dev";
      const location = process.env.GCP_TASKS_LOCATION || "us-central1";
      const queue = process.env.GCP_TASKS_QUEUE_NAME || "trajectory-execution-queue";
      this.queuePath = this.client.queuePath(project, location, queue);
    } catch (err) {
      console.warn("[GcpOrchestratorDispatcher] Failed to initialize CloudTasksClient:", err);
      this.client = null;
    }
  }

  async dispatchOrchestration(message: OrchestrateMessage): Promise<{ taskId: string; queueName: string }> {
    if (!this.client) {
      const mock = new MockOrchestratorDispatcher();
      return mock.dispatchOrchestration(message);
    }

    const payload = JSON.stringify({
      event_id: message.eventId,
      correlation_id: message.correlationId,
      segment_id: message.segmentId || "swe_coding_python_interactive",
    });

    const targetUrl = `${this.workerUrl}/orchestrate`;
    const taskName = `${this.queuePath}/tasks/orch_${message.eventId}`;

    const httpRequest: any = {
      httpMethod: "POST" as const,
      url: targetUrl,
      headers: {
        "Content-Type": "application/json",
        "X-Benchpress-Correlation-ID": message.correlationId,
      },
      body: Buffer.from(payload).toString("base64"),
    };

    const invokerServiceAccount = process.env.GCP_TASKS_INVOKER_SERVICE_ACCOUNT;
    if (invokerServiceAccount) {
      httpRequest.oidcToken = {
        serviceAccountEmail: invokerServiceAccount,
        audience: this.workerUrl,
      };
    }

    try {
      const [response] = await this.client.createTask({
        parent: this.queuePath,
        task: {
          name: taskName,
          httpRequest,
        },
      });

      return {
        taskId: response.name || taskName,
        queueName: this.queuePath,
      };
    } catch (err: any) {
      console.warn("[GcpOrchestratorDispatcher] Cloud Tasks dispatch error, falling back to direct HTTP dispatch:", err.message);
      const mock = new MockOrchestratorDispatcher();
      return mock.dispatchOrchestration(message);
    }
  }
}

class MockOrchestratorDispatcher implements IOrchestratorDispatcher {
  private workerUrl: string;

  constructor() {
    this.workerUrl = (process.env.SANDBOX_WORKER_URL || "http://localhost:8000").replace(/\/$/, "");
  }

  async dispatchOrchestration(message: OrchestrateMessage): Promise<{ taskId: string; queueName: string }> {
    const taskId = `mock-orch-${Date.now()}-${message.eventId}`;
    const payload = {
      event_id: message.eventId,
      correlation_id: message.correlationId,
      segment_id: message.segmentId || "swe_coding_python_interactive",
    };

    try {
      fetch(`${this.workerUrl}/orchestrate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).catch((err) => {
        // Best-effort local worker notify
      });
    } catch {
      // Best-effort local mock
    }

    return {
      taskId,
      queueName: "local-in-memory-orchestration-queue",
    };
  }
}

let dispatcherInstance: IOrchestratorDispatcher | null = null;

export function getOrchestratorDispatcher(): IOrchestratorDispatcher {
  if (dispatcherInstance) return dispatcherInstance;
  const useMock = process.env.USE_LOCAL_MOCK !== "false";
  dispatcherInstance = useMock ? new MockOrchestratorDispatcher() : new GcpOrchestratorDispatcher();
  return dispatcherInstance;
}
