/**
 * GET /api/v1/replays/[id]
 * Retrieves ordered state transition replay events for an experiment.
 */

import { NextRequest, NextResponse } from "next/server";
import { firestoreRepo } from "@/lib/server/firestore-repo";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const events = await firestoreRepo.getReplayEvents(id);

  return NextResponse.json({
    experiment_id: id,
    events_count: events.length,
    events,
  }, {
    headers: { "Cache-Control": "no-store, max-age=0, must-revalidate" },
  });
}
