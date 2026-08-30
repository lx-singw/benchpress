/**
 * GET /api/v1/decisions/[id]
 * Retrieves the canonical decision contract, configuration diff, and aggregate metrics.
 */

import { NextRequest, NextResponse } from "next/server";
import { firestoreRepo } from "@/lib/server/firestore-repo";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const receipt = await firestoreRepo.getDecision(id);

  if (!receipt) {
    return NextResponse.json(
      { error: "Not Found", message: `Decision receipt for '${id}' not found` },
      { status: 404 }
    );
  }

  const [baseConfig, candConfig, baseAgg, candAgg] = await Promise.all([
    firestoreRepo.getConfiguration(receipt.baseline_configuration_id),
    receipt.candidate_configuration_id
      ? firestoreRepo.getConfiguration(receipt.candidate_configuration_id)
      : null,
    firestoreRepo.getAggregate(receipt.baseline_aggregate_id),
    receipt.candidate_aggregate_id
      ? firestoreRepo.getAggregate(receipt.candidate_aggregate_id)
      : null,
  ]);

  return NextResponse.json({
    receipt_id: receipt.receipt_id,
    decision_id: receipt.decision_id,
    experiment_id: receipt.experiment_id,
    correlation_id: receipt.correlation_id,
    public_decision: receipt.public_decision,
    internal_outcome: receipt.internal_outcome,
    task_segment_id: receipt.task_segment_id,
    baseline_configuration_id: receipt.baseline_configuration_id,
    candidate_configuration_id: receipt.candidate_configuration_id,
    why_decision: receipt.why_decision,
    why_not_cheapest: receipt.why_not_cheapest,
    what_would_reverse_it: receipt.what_would_reverse_it,
    known_limitations: receipt.known_limitations,
    publication_status: receipt.publication_status,
    truth_class: receipt.truth_class,
    evidence_hash: receipt.evidence_hash,
    code_commit_sha: receipt.code_commit_sha,
    created_at: receipt.created_at,
    baseline_configuration: baseConfig,
    candidate_configuration: candConfig,
    baseline_aggregate: baseAgg,
    candidate_aggregate: candAgg,
  }, {
    headers: { "Cache-Control": "no-store, max-age=0, must-revalidate" },
  });
}
