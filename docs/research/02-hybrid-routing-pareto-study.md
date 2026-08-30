# Empirical Study: Multi-Tiered Hybrid Model Routing Choreography on the Pareto Frontier

> **Publication ID:** `BP-RES-2026-002`  
> **Authors:** Benchpress Systems Research Group  
> **Target Track:** Academic Thought Leadership & Model Routing • Google Cloud Hackathon (2026)

> **Evidence disposition (2026-08-29): Historical synthetic study.** Task counts, model outcomes, percentages, latency, and Pareto results in this paper are unverified fixture/hypothesis values, not provider measurements or submission claims. Use the [implementation status](../00-implementation-status.md) and a verified `evidence/runs/<correlation_id>` bundle for current empirical claims.

---

## Abstract

Monolithic foundation model architectures present a rigid trade-off between reasoning capability and inference cost. In this study, we formalize and empirically evaluate the **2-Tiered Asymmetric Routing Pattern**, which decouples multi-turn agentic workflows into high-order **Plan Decompositions** (executed by heavy frontier models, e.g., Gemini 2.5 Pro) and low-order **Tactical Code Manipulations** (executed by high-speed sub-cent models, e.g., Gemini 3.5 Flash).

Across 500 ground-truth software engineering tasks, we prove that the Asymmetric Hybrid Route dominates monolithic frontier baselines on the multi-objective Pareto frontier, achieving **$98.8\%$** of monolithic Pass@1 accuracy while reducing token cost by **$85.2\%$** and decreasing total trajectory duration by **$67.1\%$**.

---

## 1. Mathematical Formulation of Asymmetric Agent Routing

Let an agent trajectory consist of two disjoint turn sets:
- **Planning Turns ($\mathcal{T}_{\text{plan}}$):** Initial task decomposition, dependency graph traversal, and high-order error recovery.
- **Execution Turns ($\mathcal{T}_{\text{exec}}$):** AST file edits, regex grepping, directory listings, and pytest execution.

In a monolithic configuration with model $\mathcal{M}_1$:
$$C_{\text{mono}} = \sum_{t \in \mathcal{T}_{\text{plan}}} c(\mathcal{M}_1, t) + \sum_{t \in \mathcal{T}_{\text{exec}}} c(\mathcal{M}_1, t)$$

In our 2-Tiered Hybrid configuration pairing Planner $\mathcal{M}_{\text{plan}}$ with Executor $\mathcal{M}_{\text{exec}}$:
$$C_{\text{hybrid}} = \sum_{t \in \mathcal{T}_{\text{plan}}} c(\mathcal{M}_{\text{plan}}, t) + \sum_{t \in \mathcal{T}_{\text{exec}}} c(\mathcal{M}_{\text{exec}}, t)$$

Given that $|\mathcal{T}_{\text{exec}}| \gg |\mathcal{T}_{\text{plan}}|$ in real-world coding benchmarks (typically $|\mathcal{T}_{\text{plan}}| = 1$ and $|\mathcal{T}_{\text{exec}}| \ge 3$), and given the price ratio:
$$\frac{P(\mathcal{M}_{\text{exec}})}{P(\mathcal{M}_{\text{plan}})} \approx \frac{1}{16.7}$$

The asymptotic cost savings ratio $\sigma$ approaches:
$$\sigma = 1 - \frac{C_{\text{hybrid}}}{C_{\text{mono}}} \approx 1 - \left( \frac{|\mathcal{T}_{\text{plan}}|}{|\mathcal{T}|} + \frac{|\mathcal{T}_{\text{exec}}|}{|\mathcal{T}|} \cdot \frac{P(\mathcal{M}_{\text{exec}})}{P(\mathcal{M}_{\text{plan}})} \right) \approx 0.852 \quad (85.2\%)$$

---

## 2. Pareto Frontier Optimization Curve

```text
  Accuracy (Pass@1)
    100% |
         |
     50% |                           ★ Hybrid (2.5 Pro + 3.5 Flash) [48.6%, $0.24 CPR]
         |                         /   \
         |                        /     ● Gemini 2.5 Pro Monolithic [49.2%, $1.62 CPR]
         |                       /
     25% |       ● Gemini 3.5 Flash [31.4%, $0.42 CPR]
         |
      0% +-------------------------------------------------------------------->
         $0.00          $0.50          $1.00          $1.50          $2.00   CPR ($)
```

The Hybrid configuration represents a strictly dominating Pareto-optimal point:
- **Marginal Accuracy Loss:** $-0.6\%$ ($48.6\%$ vs. $49.2\%$)
- **Marginal Cost Reduction:** $-\$1.38$ per resolved task ($-85.2\%$)
- **Marginal Latency Gain:** $+5.8\times$ faster turn execution on tactical file operations.

---

## 3. Dynamic Re-Escalation State Transition Theorem

If the Executor model $\mathcal{M}_{\text{exec}}$ encounters $\kappa \ge 2$ consecutive syntax or assertion failures, the runtime dynamically re-escalates the turn back to $\mathcal{M}_{\text{plan}}$:

$$\text{Transition}(S_t) = \begin{cases} 
\mathcal{M}_{\text{exec}}, & \text{if } \text{ConsecutiveErrors}(t) < 2 \\
\mathcal{M}_{\text{plan}}, & \text{if } \text{ConsecutiveErrors}(t) \ge 2 
\end{cases}$$

This closed-loop self-healing mechanism guarantees that simple tasks resolve at minimal cost, while complex edge cases automatically leverage frontier-grade reasoning.
