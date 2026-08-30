/**
 * POST /api/v1/experiments
 * Ingests a new ChangeEvent, writes initial state to Firestore, and dispatches evaluation orchestration.
 */

import { NextRequest, NextResponse } from "next/server";
import { ChangeEventSchema } from "@benchpress/contracts";
import { firestoreRepo, ExperimentRecord } from "@/lib/server/firestore-repo";
import { getOrchestratorDispatcher } from "@/lib/task-dispatcher";
import { logJson } from "@/lib/server/logger";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    // 1. Validate payload against sovereign ChangeEvent Zod schema
    const parseResult = ChangeEventSchema.safeParse(body);
    if (!parseResult.success) {
      logJson({
        severity: "WARNING",
        message: "Invalid ChangeEvent payload rejected",
        errors: parseResult.error.format(),
      });
      return NextResponse.json(
        {
          error: "Invalid ChangeEvent schema",
          details: parseResult.error.format(),
        },
        { status: 400 }
      );
    }

    const event = parseResult.data;
    const experimentId = `exp_${event.correlation_id.replace(/^corr_/, "")}`;

    // 2. Persist the immutable trigger before the experiment references it.
    await firestoreRepo.saveChangeEvent(event);

    // 3. Persist initial experiment state
    const record: ExperimentRecord = {
      experiment_id: experimentId,
      correlation_id: event.correlation_id,
      event_id: event.event_id,
      state: "RECEIVED",
      state_version: 1,
      created_at: new Date().toISOString(),
    };
    await firestoreRepo.saveExperiment(record);

    // 4. Dispatch orchestration task to Cloud Tasks
    const dispatcher = getOrchestratorDispatcher();
    const dispatchRes = await dispatcher.dispatchOrchestration({
      eventId: event.event_id,
      correlationId: event.correlation_id,
      segmentId: "swe_coding_python_interactive",
    });

    logJson({
      severity: "INFO",
      message: "Orchestration task dispatched successfully",
      experiment_id: experimentId,
      correlation_id: event.correlation_id,
      task_id: dispatchRes.taskId,
    });

    return NextResponse.json(
      {
        status: "ACCEPTED",
        experiment_id: experimentId,
        correlation_id: event.correlation_id,
        event_id: event.event_id,
        task_id: dispatchRes.taskId,
        status_url: `/api/v1/experiments/${experimentId}`,
        decision_url: `/decisions/${experimentId}`,
      },
      { status: 202 }
    );
  } catch (error: any) {
    logJson({
      severity: "ERROR",
      message: "Failed to process experiment ingestion request",
      error: error.message,
    });
    return NextResponse.json(
      { error: "Internal Server Error", message: error.message },
      { status: 500 }
    );
  }
}
