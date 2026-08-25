import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { randomUUID } from "crypto";
import { getTaskQueue } from "@/lib/gcp-tasks";
import { getDatabase } from "@/lib/firestore";
import { TrajectoryStatus } from "@benchpress/telemetry";

const TrajectorySubmissionSchema = z.object({
  task_suite: z.string().min(1),
  task_id: z.string().min(1),
  model_id: z.string().min(1),
  budget_limit_usd: z.number().positive().optional().default(2.0),
  max_turns: z.number().int().min(1).max(50).optional().default(20),
  metadata: z.record(z.unknown()).optional(),
});

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const parsed = TrajectorySubmissionSchema.safeParse(body);

    if (!parsed.success) {
      return NextResponse.json(
        { error: "Invalid trajectory payload", details: parsed.error.format() },
        { status: 400 }
      );
    }

    const { task_suite, task_id, model_id, budget_limit_usd, max_turns, metadata } = parsed.data;
    const trajectoryId = `traj-${randomUUID().replace(/-/g, "").slice(0, 12)}`;
    const now = new Date().toISOString();

    // 1. Persist initial trajectory state to Firestore
    const db = getDatabase();
    await db.createTrajectory({
      trajectoryId,
      taskSuite: task_suite,
      taskId: task_id,
      modelId: model_id,
      status: TrajectoryStatus.QUEUED,
      budgetLimitUsd: budget_limit_usd,
      maxTurns: max_turns,
      currentTurn: 0,
      totalCostUsd: 0,
      createdAt: now,
      updatedAt: now,
      result: metadata,
    });

    // 2. Dispatch to Cloud Tasks Push Queue / Local Worker
    const taskQueue = getTaskQueue();
    const { taskId: enqueuedTaskId, queueName } = await taskQueue.enqueueTrajectoryTask({
      trajectoryId,
      taskSuite: task_suite,
      taskId: task_id,
      modelId: model_id,
      budgetLimitUsd: budget_limit_usd,
      maxTurns: max_turns,
      metadata,
    });

    return NextResponse.json(
      {
        status: TrajectoryStatus.QUEUED,
        trajectory_id: trajectoryId,
        task_id: enqueuedTaskId,
        queue_name: queueName,
        enqueued_at: now,
        status_url: `/api/v1/trajectories/${trajectoryId}`,
      },
      { status: 202 }
    );
  } catch (error: any) {
    return NextResponse.json(
      { error: "Failed to dispatch trajectory", message: error.message },
      { status: 500 }
    );
  }
}
