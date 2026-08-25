# ADR-002: BigQuery Telemetry Storage vs. Cloud SQL / Spanner

> **Status:** Accepted  
> **Date:** 2026-08-16  
> **Deciders:** Lead Data Architect, Principal Cloud Systems Architect  
> **Consulted:** FinOps Lead, Backend Engineering Team  

---

## 1. Context & Problem Statement

Benchpress captures deep, multi-turn telemetry across thousands of agent benchmark runs. Each trajectory generates:
- Top-level trajectory summaries (Pass@1, total tokens, CPR, bloat ratio).
- Granular turn metrics (reasoning latency, context size, token breakdowns).
- Tool execution events (arguments, schema validity, execution duration, sandbox exit codes).

The system requires a data storage architecture capable of:
1. Ingesting tens of thousands of telemetry rows per minute with low latency.
2. Executing complex analytical aggregations (e.g., 90th percentile CPR, multi-dimensional Pareto frontiers, token degradation regressions) over millions of historical rows in $< 500\,\text{ms}$.
3. Providing cost-effective long-term storage without requiring manual database indexing or sharding.

The team evaluated **BigQuery (with Storage Write API)**, **Cloud SQL (PostgreSQL with TimescaleDB)**, and **Cloud Spanner**.

---

## 2. Decision Drivers

- **Analytical Query Performance:** Fast OLAP queries across large time ranges and high-cardinality dimensions (model versions, suites, complexity tiers).
- **Ingestion Throughput & Reliability:** High-throughput streaming writes without lock contention or table bloating.
- **Cost Scaling:** Serverless pay-per-query model vs. fixed hourly provisioned compute costs.
- **Schema Evolution:** Native support for nested JSON and flexible schema updates as new agentic tools are benchmarked.

---

## 3. Considered Options

* **Option 1: BigQuery with Storage Write API & Memorystore Redis Buffer (Selected)**
* **Option 2: Cloud SQL for PostgreSQL (with TimescaleDB extension)**
* **Option 3: Google Cloud Spanner**

---

## 4. Evaluation & Trade-off Analysis

| Evaluation Criteria | Option 1: BigQuery + Write API | Option 2: Cloud SQL (TimescaleDB) | Option 3: Cloud Spanner |
| :--- | :---: | :---: | :---: |
| **Complex Aggregations (P90 CPR, Quantiles)** | **Sub-second ($< 350\text{ms}$) on 100M+ rows** | Slows significantly $> 10\text{M}$ rows | Excellent, but requires complex indexes |
| **Storage Pricing** | **\$0.020 / GB / month (\$0.010 cold)** | \$0.170 / GB / month + compute | \$0.300 / GB / month + node fees |
| **Provisioning Model** | **100% Serverless (Zero idle cost)** | Fixed VM instance running 24/7 | Minimum 1 node (\$650+/mo) |
| **Streaming Write Throughput** | Up to 100,000+ rows/sec per table | Limited by connection pools & IOPS | Very high, but expensive |
| **Point Read Latency ($< 10\text{ms}$)** | Poor ($100-300\text{ms}$ baseline) | Excellent ($1-5\text{ms}$) | Excellent ($2-8\text{ms}$) |

---

## 5. Decision Outcome

**Chosen Option: Option 1 (BigQuery with Storage Write API and a Dual-Tier Caching Model).**

### Rationale:
1. Benchpress queries are overwhelmingly **OLAP aggregations** (Pareto frontier calculations, percentile rollups, cross-model regressions) rather than transactional row-level updates. BigQuery's columnar execution engine computes percentiles across millions of rows in hundreds of milliseconds.
2. To address the point-read latency requirement for public leaderboard rendering ($< 10\,\text{ms}$), Benchpress adopts a **Dual-Tier State Architecture**:
   - **Firestore Native Mode** acts as the high-speed operational cache, storing current leaderboard ranks and active trajectory steps.
   - **BigQuery** acts as the definitive analytical source of truth, updating Firestore via continuous micro-rollups and scheduled materialization queries.

---

## 6. Consequences & Mitigations

### Positive Consequences:
- Storage and compute costs reduced by over $75\%$ compared to provisioned Spanner/Cloud SQL instances.
- Zero maintenance overhead for partition vacuuming or index rebalancing.

### Negative Consequences / Limitations:
- BigQuery queries have an inherent minimum latency floor ($\sim 150-300\,\text{ms}$).
- *Mitigation:* The public frontend reads exclusively from Firestore cache for instantaneous page loads; BigQuery is queried asynchronously for custom deep-dive FinOps simulations.
