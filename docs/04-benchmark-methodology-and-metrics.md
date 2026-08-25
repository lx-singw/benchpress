# 04. Benchmark Methodology & Metrics Formulation

## 🔬 Scientific Methodology & Principles

Benchpress adheres to three core evaluation tenets:
1. **Deterministic Ground-Truth Assertions:** No subjective LLM-as-a-judge "vibes". Every benchmark task must terminate in an automated unit test, an exact JSON diff assertion, or a verified transactional state change.
2. **End-to-End Economic Attribution:** Every token (input, output, cached, reasoning) is tracked and priced against real provider billing rates.
3. **Multi-Turn Trajectory Realism:** Models are evaluated inside live interactive sandboxes containing actual file systems, command execution tools, and network API mocks.

---

## 📐 Mathematical Formulations

### 1. Cost Per Resolution (CPR)
The **Cost Per Resolution** measures the true expected economic cost to achieve one successful task resolution.

$$\text{CPR} = \frac{\mathbb{E}[\text{Cost of Trajectory Run}]}{\text{Pass@1 Rate}}$$

Where the cost of an individual trajectory $i$ is calculated as:
$$\text{Cost}_i = (T_{\text{in}} \times P_{\text{in}}) + (T_{\text{out}} \times P_{\text{out}}) + (T_{\text{reason}} \times P_{\text{reason}}) + (T_{\text{cache}} \times P_{\text{cache}})$$

* $T_{\text{in}}, T_{\text{out}}, T_{\text{reason}}, T_{\text{cache}}$: Token counts across all conversation turns in the trajectory.
* $P_{\text{in}}, P_{\text{out}}, P_{\text{reason}}, P_{\text{cache}}$: Published dollar pricing per token for the specific model.
* $\text{Pass@1}$: Percentage of tasks resolved on the first attempt without manual human intervention.

---

### 2. Hybrid Routing Pareto Efficiency & Cost Reduction
For any task $T$ decomposed into a **Planning Phase** ($\mathcal{P}$) and an **Execution Phase** ($\mathcal{E}$):

$$\text{Cost}_{\text{Hybrid}} = \text{Cost}(\mathcal{P}, M_{\text{Frontier}}) + \text{Cost}(\mathcal{E}, M_{\text{Efficiency}})$$

$$\text{Savings \%} = \left( 1 - \frac{\text{Cost}_{\text{Hybrid}}}{\text{Cost}(\mathcal{P} + \mathcal{E}, M_{\text{Frontier}})} \right) \times 100$$

$$\text{Pareto Score} = \frac{\text{Task Success Rate}_{\text{Hybrid}}}{\text{Task Success Rate}_{\text{Frontier}}} \times \left( \frac{\text{Cost}_{\text{Frontier}}}{\text{Cost}_{\text{Hybrid}}} \right)^{\gamma}$$

*(where $\gamma$ is the enterprise cost-sensitivity exponent, default = 0.5).*

---

### 3. Trajectory Bloat Ratio (TBR) & Tool Reliability Score (TRS)
Quantifies the proportion of tokens and steps consumed by failures, invalid tool calls, and recovery loops.

$$\text{TBR} = \frac{\text{Tokens Expended on Failed Tool Calls \& Retries}}{\text{Total Trajectory Tokens}}$$

$$\text{TRS} = \left( 1 - \frac{N_{\text{Failed Tool Invocations}}}{N_{\text{Total Tool Invocations}}} \right) \times 100$$

* A model with high raw intelligence but a high **Trajectory Bloat Ratio** burns disproportionate token budgets attempting to self-correct hallucinated function arguments.

---

### 4. Context Degradation Index (CDI)
Measures the rate of accuracy decay as context history expands over $K$ conversational turns.

$$\text{CDI}(K) = \frac{\text{Accuracy at Turn } K}{\text{Accuracy at Turn 1}}$$

$$\text{Decay Slope } (\beta) = \frac{d}{dK} \left[ \text{Success Rate}(K) \right]$$

---

## 🗂️ The Three Benchmark Task Suites

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                          BENCHPRESS EVALUATION SUITES                         │
├───────────────────────────────────────────────────────────────────────────────┤
│  SUITE A: Real-World SWE & Code Patching (SWE-Bench Verified subset)          │
│  • 150 real GitHub issues from popular open-source repos.                     │
│  • Agent must inspect codebase, locate bug, edit files, and pass pytest.     │
│                                                                               │
│  SUITE B: Structured Document & Financial Reconciliation                      │
│  • Ingests 50-page complex PDFs with nested tables and messy invoices.        │
│  • Reconciles transactions against ledger databases; asserts 0 false matches.│
│                                                                               │
│  SUITE C: Multi-Step Autonomous Operational Workflows                         │
│  • 10-step API chaining (OAuth tokens, rate-limited endpoints, retry logic).  │
│  • Validates idempotent commits and transactional integrity.                  │
└───────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Live Composite Index Calculation

The **Benchpress Overall Rating (BOR)** is a weighted composite score (0–100) combining capability, economics, and reliability:

$$\text{BOR} = w_1 \cdot \text{Success Rate} + w_2 \cdot (100 - \text{Normalized CPR}) + w_3 \cdot \text{TRS} + w_4 \cdot (100 \cdot \text{CDI}_{50})$$

*Default Weights: $w_1 = 0.40, w_2 = 0.30, w_3 = 0.20, w_4 = 0.10$.*
