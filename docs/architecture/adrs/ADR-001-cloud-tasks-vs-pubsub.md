# ADR-001: Cloud Tasks vs. Pub/Sub for Deterministic Agent Dispatch

> **Status:** Accepted  
> **Date:** 2026-08-15  
> **Deciders:** Principal Cloud Systems Architect, Founding AI Engineer  
> **Consulted:** DevOps Lead, FinOps Team  

---

## 1. Context & Problem Statement

Benchpress executes large fleets of asynchronous, multi-turn AI agent benchmarks against foundation models hosted on Google Cloud Vertex AI and third-party APIs. 

Benchmark execution requires:
1. **Strict Rate Limiting & Quota Management:** Foundation model APIs enforce strict token-per-minute (TPM) and requests-per-minute (RPM) quotas. Overwhelming upstream models triggers cascading HTTP 429 errors.
2. **Deterministic Push Delivery to Serverless Workers:** Workers run inside Cloud Run Gen2 containers with gVisor sandboxing.
3. **Fine-Grained Concurrency Control:** Tasks must be dispatched with configurable concurrency limits per model family (e.g., max 50 concurrent runs for Gemini 2.5 Pro, max 200 for Gemini 3.5 Flash).
4. **Task-Level Deduplication & Cancellation:** Benchmark runs must support immediate cancellation if budget limits are hit.

The engineering team evaluated **Google Cloud Tasks** versus **Google Cloud Pub/Sub**.

---

## 2. Decision Drivers

- **Rate-Limiting Control:** Ability to define exact `max_dispatches_per_second` and `max_concurrent_dispatches` at the queue level.
- **Serverless Integration:** Native HTTP push invocation targeting private Cloud Run service endpoints without requiring always-on pull-subscriber daemons.
- **Backoff & Jitter Semantics:** Configurable exponential backoff and retry limits per task without writing complex dead-letter-queue retry loops.
- **Operational Cost & Overhead:** Zero infrastructure management overhead; pay strictly per task dispatch.

---

## 3. Considered Options

* **Option 1: Google Cloud Tasks (Selected)**
* **Option 2: Google Cloud Pub/Sub (Pull Subscription with GKE/Cloud Run Daemon)**
* **Option 3: RabbitMQ / Celery on Compute Engine**

---

## 4. Evaluation & Trade-off Analysis

| Evaluation Criteria | Option 1: Cloud Tasks | Option 2: Cloud Pub/Sub | Option 3: Celery / RabbitMQ |
| :--- | :---: | :---: | :---: |
| **Token-Bucket Rate Limiting** | **Native (Per-queue configuration)** | Manual implementation required | Native (Celery rate limits) |
| **Concurrency Throttling** | **Native (`max_concurrent_dispatches`)** | Complex partition/lease logic | Requires worker pool tuning |
| **Direct Cloud Run Invocation** | **Native HTTP Push via IAM** | Requires Push Subscription or Puller | Requires custom HTTP dispatcher |
| **Task Deduplication** | **Native (Named tasks)** | Message deduplication window (10m) | Manual Redis key locking |
| **Operational Maintenance** | **Zero (Fully Managed Serverless)** | Zero (Fully Managed Serverless) | High (VM management, HA clusters) |
| **Throughput Ceiling** | Up to 1,000 dispatches/sec per queue | $> 100,000$ msgs/sec | Up to 20,000 msgs/sec |

---

## 5. Decision Outcome

**Chosen Option: Option 1 (Google Cloud Tasks).**

### Rationale:
Cloud Tasks was designed specifically for **targeted, rate-limited invocation of serverless compute resources**. In contrast to Pub/Sub (which is optimized for high-volume fire-and-forget event streaming), Cloud Tasks provides:
1. First-class support for `max_dispatches_per_second` and `max_concurrent_dispatches`, allowing Benchpress to strictly honor Vertex AI quota envelopes without dropping tasks.
2. Direct HTTP push into private Cloud Run workers, automatically scaling worker instances from 0 to 100 based on queue depth.
3. Named task IDs (`task_{model}_{suite}_{run_id}`) preventing duplicate dispatches of identical benchmark runs.

---

## 6. Consequences & Mitigations

### Positive Consequences:
- Upstream 429 rate-limit errors from Vertex AI dropped from $18.4\%$ to $< 0.05\%$.
- Eliminated all pull-subscriber polling worker overhead, reducing idle compute costs to $\$0.00$.

### Negative Consequences / Limitations:
- Maximum throughput per queue is capped around $1,000\,\text{req/s}$.
- *Mitigation:* Benchpress shards benchmark workloads across multiple dedicated queues (e.g., `queue-gemini-pro`, `queue-gemini-flash`, `queue-external-models`).
