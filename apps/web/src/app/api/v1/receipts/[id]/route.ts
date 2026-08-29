/**
 * GET /api/v1/receipts/[id]
 * Retrieves the cryptographic DecisionReceipt content-hashed JSON object.
 */

import { NextRequest, NextResponse } from "next/server";
import { firestoreRepo } from "@/lib/server/firestore-repo";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const receipt = await firestoreRepo.getReceipt(id);

  if (!receipt) {
    return NextResponse.json(
      { error: "Not Found", message: `Cryptographic receipt '${id}' not found` },
      { status: 404 }
    );
  }

  return NextResponse.json(receipt, {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=31536000, immutable",
    },
  });
}
