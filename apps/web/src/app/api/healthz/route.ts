import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export async function GET() {
  return NextResponse.json(
    {
      status: "healthy",
      service: "benchpress-web",
      runtime_mode: process.env.RUNTIME_MODE ?? "unset",
      release_sha: process.env.RELEASE_SHA ?? "unset",
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}
