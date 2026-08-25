# ADR-006: Autonomous AST Tool Wrapper Generation vs. Naive Error Prompting

> **Status:** Accepted  
> **Date:** 2026-08-20  
> **Deciders:** Principal Autonomous Systems Architect, Founding AI Engineer  
> **Consulted:** Lead AI Systems Engineer, Core Runtime Team  

---

## 1. Context & Problem Statement

In autonomous multi-turn agent benchmarks, tactical coding models frequently suffer from **tool calling syntax rigidity and hallucinated parameter signatures**:
- **Parameter Aliasing:** Passing `regex_pattern="..."` instead of `pattern="..."` or `file_path="..."` instead of `path="..."`.
- **Non-Existent Tool Names:** Invoking `find_file()` or `grep_code()` instead of registered tools `find_by_name()` and `grep_search()`.
- **Type Coercion Mismatches:** Passing integer line ranges as strings (e.g., `"10-25"` instead of integers `start_line=10, end_line=25`).

Traditional agent runtimes respond with **naive error prompting**—injecting a system error message back into the model context (e.g., *"Error: invalid parameter 'regex_pattern'"*). In empirical benchmarks, models repeat the identical error pattern in $38\%$ of subsequent turns, consuming multiple turns of wasted token budget and often hitting turn limits.

Benchpress evaluated whether an **Autonomous Supervisor Agent (Gemini 2.5 Pro)** could synthesize dynamic, in-context Python wrapper adapters to bridge schema mismatches in real time.

---

## 2. Decision Drivers

- **Trajectory Recovery Rate:** Maximize the percentage of tool-error trajectories converted into successful resolutions.
- **Token Efficiency:** Eliminate multi-turn prompt ping-pong caused by repeated schema corrections.
- **Runtime Latency:** The healing action must execute in $< 1.5\,\text{seconds}$.
- **Sandbox Safety:** Dynamically generated code wrappers must execute strictly inside the isolated gVisor kernel without escaping to the host.

---

## 3. Considered Options

* **Option 1: Autonomous Dynamic Wrapper Synthesis via Supervisor Agent (Selected)**
  - Supervisor (Gemini 2.5 Pro) synthesizes a Python adapter function `dynamic_adapter_wrapper(**kwargs)` that coerces parameters, maps aliases, and invokes the underlying tool.
  - The wrapper is dynamically registered in the worker's runtime tool registry inside the gVisor sandbox.
* **Option 2: Naive In-Context Error Prompting**
  - Appends validation error text to context and requests a new completion from the primary model.
* **Option 3: Hardcoded Static Regex/Alias Table**
  - Maintains a manual dictionary of known aliases (e.g., `regex_pattern -> pattern`). Fails on unanticipated parameter mutations or novel tools.

---

## 4. Empirical Evaluation & Benchmark Results

We benchmarked 250 tool-error scenarios across `swe_bench_verified` within gVisor sandboxes:

| Metric | Option 1: Supervisor AST Wrapper | Option 2: Naive Error Prompting | Option 3: Static Alias Table |
| :--- | :---: | :---: | :---: |
| **Tool Error Recovery Rate (%)** | **85.6%** | 41.2% | 52.4% |
| **Mean Turns to Resolve Error** | **1.0 Turn (Instant)** | 2.8 Turns | 1.0 Turn (when matched) |
| **Wasted Bloat Tokens per Error** | **~240 Tokens** | ~3,400 Tokens | ~0 Tokens (when matched) |
| **Unanticipated Mutation Coverage** | **94.2%** | 38.0% | 0.0% (Hardcoded only) |
| **Healing Overhead Latency** | **850ms** | 2,400ms (Multi-turn) | < 1ms |

---

## 5. Decision Outcome

**Chosen Option: Option 1 (Autonomous Dynamic Wrapper Synthesis via Supervisor Agent).**

### Rationale:
1. **Unrivaled Recovery:** Converts **$85.6\%$** of repetitive tool schema failures into clean executions on the very next turn.
2. **Token Economy:** Eliminates up to 3 turns of repetitive back-and-forth prompt correction, reducing Trajectory Bloat Ratio ($\text{TBR}$) by an average of **$18.4\%$**.
3. **Adaptive Generalization:** Handles arbitrary parameter mutations and novel third-party tools submitted via community RFCs without requiring manual code changes.

---

## 6. Consequences & Mitigations

### Positive Consequences:
- Unlocks closed-loop self-healing for autonomous agent runs, significantly increasing benchmark Pass@1 resolution rates for fast coding models.

### Security Guarantees:
- Synthesized wrapper code is executed within the sandbox worker's `tmpfs` execution scope under the gVisor user-space kernel; it cannot access host resources or bypass security interceptors.
