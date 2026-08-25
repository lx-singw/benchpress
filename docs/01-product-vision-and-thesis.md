# 01. Product Vision & Core Thesis

## 💡 The One-Sentence Thesis
> **Raw token benchmarks like MMLU and dollars-per-million-tokens are obsolete in the agentic era: what matters is the true Cost Per Resolution (CPR), trajectory bloat, tool reliability, and hybrid routing economics across multi-step autonomous workflows.**

---

## 🌪️ The 2026 Problem: The Agentic Black Box
In 2026, software organizations are spending millions of dollars on AI foundation models and autonomous agent harnesses (Cursor, Windsurf, Devin, Factory, and proprietary enterprise agent loops). 

However, engineering leaders, CTOs, and FinOps teams face three critical blind spots:

### 1. The "Cheap Model" Trap (The CPR Paradox)
A model advertised at \$0.20 per million tokens sounds like a massive bargain compared to a \$10 per million token frontier model. 
* In practice, a cheaper model often suffers from **tool-calling hallucinations, malformed JSON arguments, and looping retries**.
* A task that a frontier model resolves in **1 turn (5,000 tokens = \$0.05)** might take a weaker model **12 retry turns, 80,000 wasted tokens, and 4 minutes of compute**, ending in a broken output or costing **\$0.24 (5x higher)**.
* **Current public benchmarks (Artificial Analysis, LMSYS) only publish raw token prices and static question-answering scores**, hiding the true multi-turn execution cost.

### 2. The Model Routing Blind Spot
The most cost-effective architecture in modern AI engineering is **Hybrid Model Routing**:
* **Planning / Architecture / Spec Generation:** Assigned to a frontier reasoning model (e.g., Gemini 2.5 Pro, Claude Sonnet).
* **Code Implementation / Command Execution:** Assigned to a low-cost, high-throughput model (e.g., Gemini 3.5/3.7 Flash, DeepSeek, Qwen).
* **Review & Verification:** Assigned back to the frontier model.

When implemented correctly, this routing strategy slashes monthly AI bills by **68% to 85%**. But engineering teams lack empirical data answering:
* *Which exact model pairs retain 95%+ SWE-grade task resolution?*
* *At what task complexity threshold does routing to a smaller model cause catastrophic regression?*
* *How do different thinking effort levels (e.g., 2k vs 16k reasoning tokens) impact total downstream coding costs?*

### 3. The "Why Switch?" Developer Friction
Agent harnesses (like Cursor Auto mode, Not Diamond, or custom internal company gateways) automatically switch models behind the scenes. However, developers and enterprise stakeholders frequently distrust or override these switches because there is no transparent, real-time explanation or verified benchmark rationale provided at the moment of the switch.

---

## 🏋️‍♂️ The Solution: Benchpress
**Benchpress** is the **independent economic and trajectory intelligence platform for AI agents & model routing** (the *"Artificial Analysis of the Agentic Era"*).

Benchpress combines an **autonomous background testing engine** running continuous real-world agent trajectories on Google Cloud with an **interactive public intelligence hub** and an **embeddable developer API**.

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                              BENCHPRESS PLATFORM                              │
├───────────────────────────────────────────────────────────────────────────────┤
│  1. Autonomous Background Engine: Continuously executes live agent workflows  │
│     across software engineering, document extraction, and multi-step ops.    │
│                                                                               │
│  2. BigQuery Telemetry & Analytics: Captures step-by-step token burn, tool   │
│     retries, reasoning overhead, and pass/fail states.                        │
│                                                                               │
│  3. The 4 Proprietary Indices: CPR Index, Routing Pareto Matrix, Trajectory   │
│     Bloat, and Context Degradation Curves.                                    │
│                                                                               │
│  4. Public Web Hub & Developer API: Empowers developers, CTOs, and model      │
│     routers with instant, data-backed routing rationales.                     │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 The 4 Proprietary Benchpress Indices

### 1. Cost Per Resolution (CPR) Index
Measures the **actual median dollar cost to achieve a successful task resolution** (e.g., fixing a real GitHub bug, extracting complex nested financial data from 50 PDFs, or completing a 10-step API transaction).
$$\text{CPR} = \frac{\sum (\text{Input Tokens} \times P_{\text{in}} + \text{Output Tokens} \times P_{\text{out}} + \text{Reasoning Tokens} \times P_{\text{reason}})}{\text{Task Success Rate (Pass@1)}}$$

### 2. Hybrid Routing Pareto Matrix
Maps the empirical Pareto efficiency curve for multi-model workflows. Evaluates combinations like `[Frontier Planner] + [Efficiency Coder]` to reveal the exact mathematical sweet spot between maximum cost savings and zero accuracy loss.

### 3. Trajectory Bloat & Tool Reliability Score
Quantifies the percentage of token spend wasted during an agent's execution on:
* Hallucinated function names / non-existent arguments.
* JSON parsing and schema validation errors.
* Infinite looping and redundant file lookups.

### 4. Context Degradation & Drift Curve
Tracks how model decision-making accuracy and tool invocation precision decline as the conversational history grows from 5 turns to 10, 20, and 50 turns.

---

## 🛡️ Strategic Principles
1. **Empirical Realism Over Synthetic Prompts:** Benchmarks must run on real sandboxed environments with file systems, terminal execution, and multi-step tool calls (no multiple-choice trivia).
2. **Economic Transparency:** Every score is linked directly to dollars, token counts, and execution latency.
3. **Model-Agnostic Objectivity:** Benchpress remains strictly independent, providing unbiased evaluations across Google Gemini, Anthropic Claude, OpenAI, and open-source weights (DeepSeek, Llama, Qwen).
4. **Actionable via API:** Benchpress is not just a static website; it is an active data feed queried by production routing engines in real time.
