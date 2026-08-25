# ADR-003: 2-Tiered Hybrid Model Routing Choreography

> **Status:** Accepted  
> **Date:** 2026-08-17  
> **Deciders:** Founding AI Engineer, Principal Cloud Systems Architect  
> **Consulted:** Lead Multimodal AI UX Designer, FinOps Team  

---

## 1. Context & Problem Statement

Autonomous software engineering agents require two distinct cognitive capabilities during a multi-turn trajectory:
1. **High-Order Architectural Planning & Task Decomposition:** Requires massive context assimilation, repo-wide dependency tracing, and deep reasoning (high intelligence, higher inference cost and latency).
2. **Deterministic Code Generation, File Editing & Shell Execution:** Requires strict JSON tool calling syntax conformance, fast execution speed, and high token throughput (lower reasoning overhead, low cost per token).

Historically, agent frameworks routed all turns to a single monolithic frontier model (e.g., Claude 3.7 Sonnet or Gemini 2.5 Pro), resulting in:
- High Cost Per Resolution ($\text{CPR} > \$1.80$ per task).
- Sluggish turn latency ($8-15\,\text{seconds}$ per minor file edit).
- Accelerated context exhaustion.

The engineering team investigated whether a **2-Tiered Hybrid Choreography Pattern** using **Gemini 2.5 Pro as the Planner** and **Gemini 3.5 Flash / Gemini 3.7 Flash as the Tool Executor** could optimize the Pareto frontier.

---

## 2. Decision Drivers

- **Cost Per Resolution ($\text{CPR}$):** Minimize total dollar expenditure to achieve a verified unit test fix.
- **Turn Latency ($\text{TTFT}$ & $\text{TPS}$):** Maximize developer interactivity and minimize overall trajectory wall-clock duration.
- **Pass@1 Resolution Rate:** Maintain or exceed the resolution accuracy of monolithic frontier baselines.
- **Tool Schema Precision:** Ensure zero regression in tool calling syntax and parameter adherence.

---

## 3. Considered Options

* **Option 1: 2-Tiered Hybrid Routing Choreography (Selected)**
  - *Tier 1 (Planner):* Gemini 2.5 Pro initializes the trajectory, creates the multi-step strategy, and triggers during complex self-healing branch points.
  - *Tier 2 (Coder/Executor):* Gemini 3.5 Flash executes tactical file reads, regex searches, and code edits under the guidance of the active plan.
* **Option 2: Monolithic Frontier Routing**
  - All turns routed exclusively to Gemini 2.5 Pro or Claude 3.7 Sonnet.
* **Option 3: Pure High-Speed Model Routing**
  - All turns routed exclusively to Gemini 3.5 Flash.

---

## 4. Evaluation & Benchmark Results

Benchpress evaluated these routing patterns across 500 tasks from the `swe_bench_verified` dataset:

| Metric | Option 1: Hybrid (2.5 Pro + 3.5 Flash) | Option 2: Monolithic (2.5 Pro) | Option 3: Pure Flash (3.5 Flash) |
| :--- | :---: | :---: | :---: |
| **Pass@1 Verified** | **48.6%** | 49.2% | 31.4% |
| **Mean Cost Per Resolution (CPR)** | **\$0.24** | \$1.62 | \$0.42 (Due to failed runs) |
| **Mean Total Execution Time** | **42.3 seconds** | 128.5 seconds | 29.1 seconds |
| **Trajectory Bloat Ratio (TBR)** | **11.2%** | 14.8% | 34.7% |
| **Token Cost Reduction vs. Monolithic** | **-85.2%** | 0.0% (Baseline) | -74.1% |

---

## 5. Decision Outcome

**Chosen Option: Option 1 (2-Tiered Hybrid Model Routing Choreography).**

### Rationale:
1. **Economic Superiority:** The Hybrid pattern achieves $98.8\%$ of monolithic frontier resolution accuracy while slashing Cost Per Resolution by **$85.2\%$** ($\$0.24$ vs. $\$1.62$).
2. **Speed & UX:** File navigation and multi-file search turns execute in $< 1.2\,\text{seconds}$ on Gemini 3.5 Flash, providing fluid live updates to developers.
3. **Resilience:** If Gemini 3.5 Flash encounters $> 2$ consecutive failed test assertions, the runtime dynamically re-escalates the turn to Gemini 2.5 Pro for deep plan revision.

---

## 6. Consequences & Mitigations

### Positive Consequences:
- Enables Benchpress to serve real-time model routing recommendations to IDEs (Cursor, Windsurf) that save engineering teams tens of thousands of dollars monthly in LLM spend.

### Architectural Requirements:
- The FSM runtime must track conversational turn roles and inject plan checkpoints into context when transitioning between Planner and Executor models.
