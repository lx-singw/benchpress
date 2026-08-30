import { test } from "node:test";
import assert from "node:assert/strict";
import { NextRequest } from "next/server";
import { POST as handleExperimentPost } from "../../src/app/api/v1/experiments/route";
import { GET as handleExperimentGet } from "../../src/app/api/v1/experiments/[id]/route";
import { GET as handleDecisionGet } from "../../src/app/api/v1/decisions/[id]/route";
import { GET as handleReceiptGet } from "../../src/app/api/v1/receipts/[id]/route";
import { GET as handleReplayGet } from "../../src/app/api/v1/replays/[id]/route";
import { DecisionReceiptSchema, ReplayEventSchema } from "@benchpress/contracts";
import { generateReceiptId, TruthClass } from "@benchpress/contracts";
import { FirestoreMeasuredRepository } from "../../src/lib/server/firestore-repo";

test("Decision API Endpoints & Contract Verification", async (t) => {
  await t.test("GET /api/v1/decisions/[id] returns valid decision and aggregates", async () => {
    const req = new NextRequest("http://localhost:3000/api/v1/decisions/exp_01J6G7R8Q9ABCDEFGHJKMNPQ20");
    const res = await handleDecisionGet(req, { params: Promise.resolve({ id: "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20" }) });

    assert.equal(res.status, 200);
    const data = await res.json();

    assert.equal(data.public_decision, "SWITCH");
    assert.equal(data.truth_class, "DEMO_FIXTURE");
    assert.ok(data.evidence_hash);
    assert.ok(data.baseline_configuration);
    assert.ok(data.candidate_configuration);
    assert.ok(data.baseline_aggregate);
    assert.ok(data.candidate_aggregate);
  });

  await t.test("GET /api/v1/receipts/[id] returns sovereign DecisionReceipt schema", async () => {
    const req = new NextRequest("http://localhost:3000/api/v1/receipts/rcpt_0123456789abcdef");
    const res = await handleReceiptGet(req, { params: Promise.resolve({ id: "rcpt_0123456789abcdef" }) });

    assert.equal(res.status, 200);
    const data = await res.json();

    // Validate with sovereign Zod schema
    const parseResult = DecisionReceiptSchema.safeParse(data);
    assert.ok(parseResult.success, `Schema validation failed: ${JSON.stringify(parseResult.error?.format())}`);
    assert.equal(data.receipt_id, "rcpt_0123456789abcdef");
    assert.equal(data.public_decision, "SWITCH");
  });

  await t.test("GET /api/v1/replays/[id] returns ordered ReplayEvents", async () => {
    const req = new NextRequest("http://localhost:3000/api/v1/replays/exp_01J6G7R8Q9ABCDEFGHJKMNPQ20");
    const res = await handleReplayGet(req, { params: Promise.resolve({ id: "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20" }) });

    assert.equal(res.status, 200);
    const data = await res.json();

    assert.equal(data.experiment_id, "exp_01J6G7R8Q9ABCDEFGHJKMNPQ20");
    assert.ok(data.events.length >= 7);
    for (const evt of data.events) {
      const parseResult = ReplayEventSchema.safeParse(evt);
      assert.ok(parseResult.success, `ReplayEvent validation failed: ${JSON.stringify(parseResult.error?.format())}`);
    }
  });

  await t.test("GET /api/v1/decisions/unknown_id returns 404 Not Found", async () => {
    const req = new NextRequest("http://localhost:3000/api/v1/decisions/exp_nonexistent_9999");
    const res = await handleDecisionGet(req, { params: Promise.resolve({ id: "exp_nonexistent_9999" }) });

    assert.equal(res.status, 404);
  });

  await t.test("POST /api/v1/experiments accepts valid ChangeEvent and returns 202", async () => {
    const validEvent = {
      schema_version: "1.0.0",
      event_id: "evt_01J6G7R8Q9ABCDEFGHJKMNPQ01",
      correlation_id: "corr_01J6G7R8Q9ABCDEFGHJKMNPQ02",
      event_type: "PRICE_CHANGE",
      source_kind: "PROVIDER_CATALOG",
      source_reference: "https://ai.google.dev/pricing",
      target_provider: "google",
      target_model_family: "gemini-2.5",
      changed_fields: [
        "price_input_per_million_usd",
        "price_output_per_million_usd"
      ],
      source_checksum: "a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0a0",
      effective_at: "2026-08-29T10:00:00.000Z",
      retrieved_at: "2026-08-29T10:00:05.000Z",
      baseline_policy_version: "pol_01J6G7R8Q9ABCDEFGHJKMNPQ10",
      baseline_configuration_id: "cfg_948a3f81e3a1b029",
      max_spend_usd: "2.500000",
      deadline_at: "2026-08-29T10:30:00.000Z",
      initiator: "catalog_sweep_daemon",
      replay: false,
      replay_label: "prod_sweep_20260829",
      created_at: "2026-08-29T10:00:05.000Z"
    };

    const req = new NextRequest("http://localhost:3000/api/v1/experiments", {
      method: "POST",
      body: JSON.stringify(validEvent),
      headers: { "Content-Type": "application/json" },
    });

    const res = await handleExperimentPost(req);
    assert.equal(res.status, 202);
    const data = await res.json();
    assert.equal(data.status, "ACCEPTED");
    assert.ok(data.experiment_id);
    assert.ok(data.status_url);
  });

  await t.test("POST /api/v1/experiments rejects invalid payload with 400", async () => {
    const invalidEvent = { invalid_field: true };
    const req = new NextRequest("http://localhost:3000/api/v1/experiments", {
      method: "POST",
      body: JSON.stringify(invalidEvent),
      headers: { "Content-Type": "application/json" },
    });

    const res = await handleExperimentPost(req);
    assert.equal(res.status, 400);
  });
});

test("Measured read model rejects unpublished and invalid-digest receipts", async () => {
  const localReq = new NextRequest("http://localhost:3000/api/v1/receipts/rcpt_0123456789abcdef");
  const localRes = await handleReceiptGet(localReq, { params: Promise.resolve({ id: "rcpt_0123456789abcdef" }) });
  const fixture = await localRes.json();
  const measuredBody = {
    ...fixture,
    receipt_id: undefined,
    truth_class: TruthClass.BENCHPRESS_MEASURED,
    code_commit_sha: "1".repeat(40),
  };
  delete measuredBody.receipt_id;
  const receipt = { ...measuredBody, receipt_id: generateReceiptId(measuredBody) };
  const experimentId = receipt.experiment_id;

  const documents = new Map<string, unknown>([
    [`benchpress_published_decisions/${experimentId}`, {
      experiment_id: experimentId,
      receipt_id: receipt.receipt_id,
      publication_status: "PUBLISHED",
    }],
    [`benchpress_decision_receipts/${receipt.receipt_id}`, receipt],
  ]);
  const fakeClient = {
    collection(name: string) {
      return {
        doc(id: string) {
          return {
            async get() {
              const data = documents.get(`${name}/${id}`);
              return { exists: data !== undefined, data: () => data, get: (key: string) => (data as any)?.[key] };
            },
          };
        },
      };
    },
  };
  const repo = new FirestoreMeasuredRepository(fakeClient as any);
  assert.equal((await repo.getDecision(experimentId))?.receipt_id, receipt.receipt_id);

  documents.set(`benchpress_decision_receipts/${receipt.receipt_id}`, { ...receipt, why_decision: "tampered" });
  assert.equal(await repo.getDecision(experimentId), null);

  documents.set(`benchpress_decision_receipts/${receipt.receipt_id}`, receipt);
  documents.set(`benchpress_published_decisions/${experimentId}`, {
    experiment_id: experimentId,
    receipt_id: receipt.receipt_id,
    publication_status: "DRAFT",
  });
  assert.equal(await repo.getDecision(experimentId), null);
});
