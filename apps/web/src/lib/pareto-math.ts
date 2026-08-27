/**
 * Client-Side Multi-Objective 2D Pareto Efficient Frontier Algorithm.
 */

import { ModelLeaderboardEntry, ParetoPoint } from "./types";

export interface ParetoFilterWeights {
  accuracyWeight: number; // 0.0 to 1.0 (default: 0.5)
  costWeight: number; // 0.0 to 1.0 (default: 0.5)
  maxLatencySlaSec: number; // Max latency ceiling (default: 35s)
}

export class ParetoMath {
  /**
   * Identify all Pareto non-dominated operating points and compute dynamic efficiency scores.
   * Point A dominates Point B if:
   * (PassRate_A >= PassRate_B and CPR_A <= CPR_B) with at least one strictly better inequality.
   */
  public static computeParetoFrontier(
    models: ModelLeaderboardEntry[],
    weights: ParetoFilterWeights
  ): ParetoPoint[] {
    const validModels = models.filter((m) => m.mean_latency_sec <= weights.maxLatencySlaSec);

    // Normalize metrics for scoring:
    // Max Pass: 1.0 (higher is better)
    // Min CPR: $0.05 to $2.00 (lower is better)
    const maxPass = Math.max(...validModels.map((m) => m.pass_at_1), 0.01);
    const maxCpr = Math.max(...validModels.map((m) => m.cpr_usd), 0.01);

    // 1. Calculate weighted efficiency score for each model
    const scoredPoints: ParetoPoint[] = validModels.map((m) => {
      const normAccuracy = m.pass_at_1 / maxPass;
      const normCost = 1.0 - m.cpr_usd / (maxCpr * 1.2); // Inverted (lower cost -> higher score)

      const efficiencyScore =
        weights.accuracyWeight * normAccuracy + weights.costWeight * Math.max(0, normCost);

      return {
        model_id: m.model_id,
        name: m.name,
        provider: m.provider,
        cpr_usd: m.cpr_usd,
        pass_at_1: m.pass_at_1,
        latency_sec: m.mean_latency_sec,
        efficiency_score: Math.round(efficiencyScore * 1000) / 1000,
        is_pareto_frontier: false,
        is_recommended: false,
      };
    });

    // 2. Identify Non-Dominated Pareto Set
    for (let i = 0; i < scoredPoints.length; i++) {
      let isDominated = false;
      for (let j = 0; j < scoredPoints.length; j++) {
        if (i !== j) {
          const a = scoredPoints[i];
          const b = scoredPoints[j];
          // Does B dominate A?
          if (
            b.pass_at_1 >= a.pass_at_1 &&
            b.cpr_usd <= a.cpr_usd &&
            (b.pass_at_1 > a.pass_at_1 || b.cpr_usd < a.cpr_usd)
          ) {
            isDominated = true;
            break;
          }
        }
      }
      scoredPoints[i].is_pareto_frontier = !isDominated;
    }

    // 3. Mark the Top Recommended Operating Point (Highest efficiency score among Pareto set)
    let bestScore = -1;
    let bestIdx = -1;
    for (let i = 0; i < scoredPoints.length; i++) {
      if (scoredPoints[i].is_pareto_frontier && scoredPoints[i].efficiency_score > bestScore) {
        bestScore = scoredPoints[i].efficiency_score;
        bestIdx = i;
      }
    }

    if (bestIdx !== -1) {
      scoredPoints[bestIdx].is_recommended = true;
    }

    return scoredPoints.sort((a, b) => a.cpr_usd - b.cpr_usd);
  }
}
