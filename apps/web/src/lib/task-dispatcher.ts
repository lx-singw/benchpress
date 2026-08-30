/** Cloud Tasks dispatcher for the judged orchestration path. */

import { createHash } from "crypto";
import { CloudTasksClient } from "@google-cloud/tasks";

export interface OrchestrateMessage {
  eventId: string;
  correlationId: string;
  segmentId?: string;
}

export interface IOrchestratorDispatcher {
  dispatchOrchestration(message: OrchestrateMessage): Promise<{ taskId: string; queueName: string }>;
}

function runtimeMode(): string {
  return process.env.RUNTIME_MODE || "local_mock";
}

function requiredEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) throw new Error(name + " is required outside local_mock mode");
  return value;
}

function orchestrationTaskId(eventId: string): string {
  const digest = createHash("sha256").update("orchestrate:" + eventId).digest("hex").slice(0, 32);
  return "orchestrate-" + digest;
}

class GcpOrchestratorDispatcher implements IOrchestratorDispatcher {
  private client: CloudTasksClient;
  private queuePath: string;
  private workerUrl: string;
  private audience: string;
  private invokerServiceAccount: string;

  constructor(client?: CloudTasksClient) {
    if (runtimeMode() === "local_mock") {
      throw new Error("GCP dispatcher cannot be constructed in local_mock mode");
    }
    this.client = client || new CloudTasksClient();
    const project = requiredEnv("GOOGLE_CLOUD_PROJECT");
    const location = requiredEnv("GCP_TASKS_LOCATION");
    const queue = requiredEnv("GCP_TASKS_QUEUE_NAME");
    this.workerUrl = requiredEnv("SANDBOX_WORKER_URL").replace(/\/$/, "");
    this.audience = requiredEnv("TASKS_OIDC_AUDIENCE").replace(/\/$/, "");
    this.invokerServiceAccount = requiredEnv("GCP_TASKS_INVOKER_SERVICE_ACCOUNT");
    if (!this.workerUrl.startsWith("https://") || !this.audience.startsWith("https://")) {
      throw new Error("Worker URL and OIDC audience must use HTTPS outside local_mock mode");
    }
    this.queuePath = this.client.queuePath(project, location, queue);
  }

  async dispatchOrchestration(message: OrchestrateMessage): Promise<{ taskId: string; queueName: string }> {
    const payload = JSON.stringify({
      event_id: message.eventId,
      correlation_id: message.correlationId,
      segment_id: message.segmentId || "swe_coding_python_interactive",
    });
    const taskName = this.queuePath + "/tasks/" + orchestrationTaskId(message.eventId);

    try {
      const [response] = await this.client.createTask({
        parent: this.queuePath,
        task: {
          name: taskName,
          httpRequest: {
            httpMethod: "POST" as const,
            url: this.workerUrl + "/orchestrate",
            headers: {
              "Content-Type": "application/json",
              "X-Benchpress-Correlation-ID": message.correlationId,
            },
            body: Buffer.from(payload).toString("base64"),
            oidcToken: {
              serviceAccountEmail: this.invokerServiceAccount,
              audience: this.audience,
            },
          },
        },
      });
      return { taskId: response.name || taskName, queueName: this.queuePath };
    } catch (error: any) {
      if (error?.code === 6 || error?.code === "ALREADY_EXISTS") {
        return { taskId: taskName, queueName: this.queuePath };
      }
      throw error;
    }
  }
}

class MockOrchestratorDispatcher implements IOrchestratorDispatcher {
  async dispatchOrchestration(message: OrchestrateMessage): Promise<{ taskId: string; queueName: string }> {
    return {
      taskId: "mock-" + orchestrationTaskId(message.eventId),
      queueName: "local-in-memory-orchestration-queue",
    };
  }
}

let dispatcherInstance: IOrchestratorDispatcher | null = null;

export function getOrchestratorDispatcher(): IOrchestratorDispatcher {
  if (dispatcherInstance) return dispatcherInstance;
  dispatcherInstance = runtimeMode() === "local_mock"
    ? new MockOrchestratorDispatcher()
    : new GcpOrchestratorDispatcher();
  return dispatcherInstance;
}

export { GcpOrchestratorDispatcher, MockOrchestratorDispatcher, orchestrationTaskId };
