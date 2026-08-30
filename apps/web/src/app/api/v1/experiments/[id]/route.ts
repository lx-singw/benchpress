/**
 * GET /api/v1/experiments/[id]
 * Retrieves workflow execution status and state progression for an experiment.
 */

import { NextRequest, NextResponse } from "next/server";
import { firestoreRepo } from "@/lib/server/firestore-repo";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const experiment = await firestoreRepo.getExperiment(id);

  if (!experiment) {
    return NextResponse.json(
      { error: "Not Found", message: `Experiment '${id}' not found` },
      { status: 404 }
    );
  }

  return NextResponse.json({
    experiment_id: experiment.experiment_id,
    correlation_id: experiment.correlation_id,
    event_id: experiment.event_id,
    state: experiment.state,
    state_version: experiment.state_version,
    decision_id: experiment.decision_id,
    receipt_id: experiment.receipt_id,
    decision_url: experiment.decision_id ? `/decisions/${experiment.experiment_id}` : null,
    created_at: experiment.created_at,
    updated_at: experiment.updated_at || experiment.created_at,
  }, {
    headers: { "Cache-Control": "no-store, max-age=0, must-revalidate" },
  });
}
