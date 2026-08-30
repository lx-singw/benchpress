# Benchpress evidence directory

> **Truth status:** `DEMO_FIXTURE`
>
> **Eligible for publication:** `false`
>
> **Audit date:** 2026-08-29

The JSON files currently stored directly in this directory were generated from hard-coded examples. They were not exported from Firestore, Google Cloud Tasks, Cloud Run, Cloud Logging, or a retained provider execution. Their identifiers, revisions, URLs, metrics, decisions, hashes, and timestamps are synthetic and must not be described as observed, production, ground truth, or verified.

## Current fixture files

| File | Classification | Intended use |
|---|---|---|
| [`judged_run_receipt.json`](./judged_run_receipt.json) | `DEMO_FIXTURE` | Receipt-schema and decision-card development |
| [`correlation_trace.json`](./correlation_trace.json) | `DEMO_FIXTURE` | Replay timeline development |
| [`cloud_run_revisions.json`](./cloud_run_revisions.json) | `DEMO_FIXTURE` | Deployment-metadata layout development |
| [`fixture-manifest.json`](./fixture-manifest.json) | `DEMO_FIXTURE` | Machine-readable exclusion and provenance policy |

These files are explicitly ineligible for measured aggregation, recommendation selection, submission evidence, or cryptographic proof claims. A hash of a synthetic document proves only that the document bytes are stable; it does not prove that the events occurred.

## Required verified bundle

The remediation plan requires future real evidence under:

```text
evidence/runs/<correlation_id>/
  manifest.json
  README.md
  firestore/
  cloud-tasks/
  cloud-run/
  logs/
  provider/
  public-api/
  tests/
  screenshots/
  checksums.sha256
  verification-report.json
```

That directory must be created by an exporter that reads actual systems and must pass an independent offline verifier. Until such a bundle exists, there is no retained judged-run evidence in this repository.
