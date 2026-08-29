#!/usr/bin/env node
import { readFileSync } from "fs";
import { computeCanonicalHash, canonicalJsonStringify } from "../src/hashing.js";
import {
  ChangeEventSchema,
  TaskFingerprintSchema,
  NativeConfigurationSchema,
  ExperimentPlanSchema,
  RunManifestSchema,
  RunResultSchema,
  AggregateSchema,
  PolicyVersionSchemaObj,
  CanaryResultSchema,
  DecisionReceiptSchema,
  ReplayEventSchema,
  StalenessEventSchema,
} from "../src/zod.js";

const schemas: Record<string, any> = {
  "change-event": ChangeEventSchema,
  "task-fingerprint": TaskFingerprintSchema,
  "native-configuration": NativeConfigurationSchema,
  "experiment-plan": ExperimentPlanSchema,
  "run-manifest": RunManifestSchema,
  "run-result": RunResultSchema,
  "aggregate": AggregateSchema,
  "policy-version": PolicyVersionSchemaObj,
  "canary-result": CanaryResultSchema,
  "decision-receipt": DecisionReceiptSchema,
  "replay-event": ReplayEventSchema,
  "staleness-event": StalenessEventSchema,
};

async function main() {
  const args = process.argv.slice(2);
  const command = args[0];

  if (command === "hash-file") {
    const filePath = args[1];
    const raw = readFileSync(filePath, "utf8");
    const parsed = JSON.parse(raw);
    const hash = computeCanonicalHash(parsed);
    process.stdout.write(hash);
  } else if (command === "canonical-json") {
    const filePath = args[1];
    const raw = readFileSync(filePath, "utf8");
    const parsed = JSON.parse(raw);
    const canonical = canonicalJsonStringify(parsed);
    process.stdout.write(canonical);
  } else if (command === "validate") {
    const schemaName = args[1];
    const filePath = args[2];
    const schema = schemas[schemaName];
    if (!schema) {
      console.error(JSON.stringify({ valid: false, error: `Unknown schema: ${schemaName}` }));
      process.exit(1);
    }
    try {
      const raw = readFileSync(filePath, "utf8");
      const parsed = JSON.parse(raw);
      const result = schema.safeParse(parsed);
      if (result.success) {
        console.log(JSON.stringify({ valid: true, hash: computeCanonicalHash(parsed) }));
      } else {
        console.log(JSON.stringify({ valid: false, error: result.error.format() }));
      }
    } catch (err: any) {
      console.log(JSON.stringify({ valid: false, error: err.message }));
    }
  } else {
    console.error(`Usage: node cli.ts [hash-file|canonical-json|validate] ...`);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
