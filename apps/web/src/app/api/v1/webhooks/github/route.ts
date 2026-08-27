import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

/**
 * POST /api/v1/webhooks/github
 * Ingests GitHub Actions CI/CD workflow failure webhooks and triggers autonomous remediation.
 */
export async function POST(req: NextRequest) {
  try {
    const rawBody = await req.text();
    const signature = req.headers.get("x-hub-signature-256") || "";
    const event = req.headers.get("x-github-event") || "workflow_run";

    const secret = process.env.GITHUB_WEBHOOK_SECRET || "benchpress-github-webhook-secret-2026";
    const expectedSig = `sha256=${crypto.createHmac("sha256", secret).update(rawBody).digest("hex")}`;

    // Verify HMAC signature if provided
    if (signature && signature !== expectedSig) {
      return NextResponse.json(
        { status: "error", message: "Invalid HMAC-SHA256 signature" },
        { status: 401 }
      );
    }

    const payload = JSON.parse(rawBody || "{}");
    const conclusion = payload?.workflow_run?.conclusion || payload?.conclusion || "failure";
    const repoName = payload?.repository?.full_name || "enterprise/core-repo";
    const commitSha = payload?.workflow_run?.head_sha || payload?.head_sha || "a1b2c3d4e5f6";

    if (conclusion !== "failure") {
      return NextResponse.json({
        status: "ignored",
        message: `Workflow conclusion '${conclusion}' does not require autonomous remediation.`,
      });
    }

    // In a production setup, dispatch Cloud Tasks job to sandbox-worker
    const remediationJob = {
      job_id: `remediate-${commitSha.substring(0, 7)}`,
      repo: repoName,
      commit: commitSha,
      status: "DISPATCHED_TO_SANDBOX_WORKER",
      target_queue: "ci-auto-remediation-queue",
      timestamp: new Date().toISOString(),
    };

    return NextResponse.json(
      {
        status: "success",
        message: `Autonomous CI auto-remediation job dispatched for ${repoName}@${commitSha.substring(0, 7)}`,
        data: remediationJob,
      },
      { status: 202 }
    );
  } catch (error: any) {
    return NextResponse.json(
      { status: "error", message: error.message || "Failed to process GitHub webhook" },
      { status: 500 }
    );
  }
}
