/**
 * Cloud Tasks Dispatcher with Pluggable Adapter Pattern & Zero-Config Local Fallback.
 */

export interface TrajectoryTaskMessage {
  trajectoryId: string;
  taskSuite: string;
  taskId: string;
  modelId: string;
  budgetLimitUsd: number;
  maxTurns: number;
  metadata?: Record<string, unknown>;
}

export interface ITaskQueue {
  enqueueTrajectoryTask(message: TrajectoryTaskMessage): Promise<{ taskId: string; queueName: string }>;
}

class GcpCloudTasksAdapter implements ITaskQueue {
  private client: any;
  private queuePath: string;
  private workerUrl: string;

  constructor() {
    // Dynamic import / instantiation to avoid hard failure when GCP credentials are not set
    const { CloudTasksClient } = require("@google-cloud/tasks");
    this.client = new CloudTasksClient();
    const project = process.env.GOOGLE_CLOUD_PROJECT || "benchpress-dev";
    const location = process.env.GCP_TASKS_LOCATION || "us-central1";
    const queue = process.env.GCP_TASKS_QUEUE_NAME || "trajectory-execution-queue";
    this.queuePath = this.client.queuePath(project, location, queue);
    this.workerUrl = process.env.SANDBOX_WORKER_URL || "http://localhost:8080/execute-task";
  }

  async enqueueTrajectoryTask(message: TrajectoryTaskMessage): Promise<{ taskId: string; queueName: string }> {
    const payload = JSON.stringify({
      trajectory_id: message.trajectoryId,
      task_suite: message.taskSuite,
      task_id: message.taskId,
      model_id: message.modelId,
      budget_limit_usd: message.budgetLimitUsd,
      max_turns: message.maxTurns,
    });

    const task = {
      httpRequest: {
        httpMethod: "POST" as const,
        url: this.workerUrl,
        headers: {
          "Content-Type": "application/json",
          "X-Benchpress-Trajectory-ID": message.trajectoryId,
        },
        body: Buffer.from(payload).toString("base64"),
      },
    };

    const [response] = await this.client.createTask({
      parent: this.queuePath,
      task,
    });

    return {
      taskId: response.name || `task-${message.trajectoryId}`,
      queueName: this.queuePath,
    };
  }
}

class MockTaskQueueAdapter implements ITaskQueue {
  private workerUrl: string;

  constructor() {
    this.workerUrl = process.env.SANDBOX_WORKER_URL || "http://localhost:8080/execute-task";
  }

  async enqueueTrajectoryTask(message: TrajectoryTaskMessage): Promise<{ taskId: string; queueName: string }> {
    const taskId = `mock-task-${Date.now()}-${message.trajectoryId.slice(0, 8)}`;
    
    // Attempt asynchronous dispatch to local sandbox worker if reachable, otherwise log
    const payload = {
      trajectory_id: message.trajectoryId,
      task_suite: message.taskSuite,
      task_id: message.taskId,
      model_id: message.modelId,
      budget_limit_usd: message.budgetLimitUsd,
      max_turns: message.maxTurns,
    };

    try {
      fetch(this.workerUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).catch((err) => {
        console.warn(`[MockTaskQueue] Local worker not reachable at ${this.workerUrl} (simulating queue acceptance):`, err.message);
      });
    } catch {
      // Best-effort local mock
    }

    return {
      taskId,
      queueName: "local-in-memory-queue",
    };
  }
}

let taskQueueInstance: ITaskQueue | null = null;

export function getTaskQueue(): ITaskQueue {
  if (taskQueueInstance) return taskQueueInstance;

  const useMock = process.env.USE_LOCAL_MOCK === "true" || !process.env.GOOGLE_CLOUD_PROJECT;
  if (useMock) {
    taskQueueInstance = new MockTaskQueueAdapter();
  } else {
    try {
      taskQueueInstance = new GcpCloudTasksAdapter();
    } catch {
      console.warn("[TaskQueue] Falling back to MockTaskQueueAdapter due to GCP initialization error");
      taskQueueInstance = new MockTaskQueueAdapter();
    }
  }

  return taskQueueInstance;
}
