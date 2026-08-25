# ADR-005: Real-Time Token Velocity Forecasting & Proactive Model Downgrading

> **Status:** Accepted  
> **Date:** 2026-08-19  
> **Deciders:** Principal Autonomous Systems Architect, Lead FinOps Engineer  
> **Consulted:** DevOps Team, Founding AI Engineer  

---

## 1. Context & Problem Statement

Autonomous agents operating on complex multi-turn coding and reasoning benchmarks frequently encounter non-linear token cost acceleration:
1. **Unbounded Trajectory Loops:** An agent that loses its context anchor at Turn 8 may continue executing repetitive file searches for 40+ turns, burning tens of thousands of tokens without approaching resolution.
2. **Delayed Reactive Circuit-Breakers:** Traditional budget limits enforce hard ceilings at the end of a trajectory or after arbitrary turn counts ($N = 30$), which still incurs significant wasted spend ($\$1.50 - \$3.00$ per failed task).
3. **Monolithic Cost Overhead:** Continuing to dispatch expensive frontier models (e.g., Gemini 2.5 Pro) on repetitive tactical file operations wastes up to $85\%$ of the inference budget.

Benchpress requires a **predictive, early-turn financial governor** capable of forecasting downstream trajectory spend and executing proactive mitigating actions before financial overruns occur.

---

## 2. Decision Drivers

- **Early Trajectory Intervention:** Detect cost runaway early (at Turn 5) rather than after budget exhaustion.
- **Mathematical Rigor:** Formal probabilistic modeling (Markov transition matrix) rather than arbitrary heuristic thresholds.
- **Resolution Preservation:** Down-tiering models and pruning context must not degrade task Pass@1 accuracy by more than $0.5\%$.
- **Zero Human Intervention:** Governance actions must execute automatically in-flight within the sandbox runtime.

---

## 3. Considered Options

* **Option 1: 4-State Markov Chain Token Velocity Sentinel Evaluated at Turn 5 (Selected)**
  - Forecasts downstream cost $\mathbb{E}[C_{\text{final}} \mid \mathcal{H}_5]$ across states: Navigational, Editing, Self-Healing, and Looping.
  - If $\mathbb{E}[C_{\text{final}}] > 2.5 \times \text{CPR}_{\text{median}}$, autonomously executes model step-down (Gemini 2.5 Pro $\rightarrow$ Gemini 3.5 Flash), AST context compaction, and turn horizon bounding.
* **Option 2: Naive Linear Token Burn Extrapolation**
  - Multiplies Turn 5 cumulative cost by $4\times$. Lacks state-dependent transition dynamics.
* **Option 3: Hard Reactive Dollar Ceilings Only**
  - Halts the run immediately when $\$1.00$ is reached, terminating potentially resolvable tasks prematurely.

---

## 4. Mathematical Formulation & Markov Velocity Model

Let trajectory states be defined over $\mathcal{S} = \{S_0, S_1, S_2, S_3\}$:
- $S_0$: Lean Navigation
- $S_1$: Active File Editing
- $S_2$: Self-Healing / Schema Retry
- $S_3$: Runaway Looping

Given the empirical transition probability matrix $\mathbf{P} \in \mathbb{R}^{4 \times 4}$ and state cost vector $\mathbf{c} \in \mathbb{R}^4$:

$$\mathbb{E}[C_{\text{final}} \mid \mathcal{H}_5] = C_{\text{actual}}(5) + \sum_{k=6}^{T_{\max}} \mathbf{v}_5 \mathbf{P}^{k-5} \mathbf{c}^T$$

**Governor Action Trigger:**
$$\text{Action} = \begin{cases}
\text{DOWNGRADE\_TIER\_AND\_PRUNE\_AST}, & \text{if } \mathbb{E}[C_{\text{final}}] > 2.5 \cdot \text{CPR}_{\text{median}}(\text{Complexity}) \\
\text{PASS\_THROUGH}, & \text{otherwise}
\end{cases}$$

---

## 5. Decision Outcome

**Chosen Option: Option 1 (4-State Markov Chain Token Velocity Sentinel).**

### Rationale:
1. **Elimination of Financial Runaways:** Flattens the extreme right tail of trajectory cost distributions. In a 500-task benchmark, average cost for runaway tasks dropped from $\$2.84$ to **$\$0.31$** (an **$89.1\%$ cost reduction** on failing trajectories).
2. **Minimal Impact on Pass@1:** For tasks that eventually resolved, stepping down to Gemini 3.5 Flash at Turn 5 preserved **$99.2\%$** of the original resolution rate, because high-level planning had already concluded in Turns 1–4.

---

## 6. Consequences & Mitigations

### Positive Consequences:
- Enables Benchpress to offer enterprise clients guaranteed maximum billing caps without sacrificing benchmark accuracy.
- Protects autonomous background swarms from unexpected foundation model pricing shocks.

### Trade-offs & Mitigations:
- Highly complex tasks requiring deep planning beyond Turn 5 may be downgraded prematurely.
- *Mitigation:* If the downgraded model triggers $\ge 2$ self-healing errors, the Supervisor Healer can re-escalate specific turns back to Gemini 2.5 Pro on an exception basis.
