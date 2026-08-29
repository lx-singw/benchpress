"""
Failure-Inclusive Aggregator.
Computes mathematically rigorous pass rates, CPR ($), latency, and confidence intervals across all attempts.
"""

import math
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Any, Tuple
from contracts.models import RunResult, Aggregate
from contracts.states import UncertaintyMethod
from contracts.hashing import generate_aggregate_id, utc_now_rfc3339


def calculate_wilson_score_interval(
    successes: int,
    total: int,
    confidence: float = 0.95,
) -> Tuple[float, float]:
    """Calculate Wilson Score Interval for binomial proportion."""
    if total <= 0:
        return 0.0, 1.0

    z = 1.96 if confidence == 0.95 else 2.576 # 95% or 99%
    p_hat = successes / total
    z2 = z * z
    n = total

    denominator = 1 + z2 / n
    center = (p_hat + z2 / (2 * n)) / denominator
    spread = (z * math.sqrt((p_hat * (1 - p_hat) + z2 / (4 * n)) / n)) / denominator

    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return round(lower, 4), round(upper, 4)


class ConfigurationAggregator:
    """Aggregates execution results for a single configuration."""

    def aggregate_runs(
        self,
        experiment_id: str,
        correlation_id: str,
        configuration_id: str,
        results: List[RunResult],
        aggregation_policy_version: str = "agg_pol_v1_taskmaster",
        quality_floor: float = 0.75,
    ) -> Aggregate:
        """
        Aggregate results for a configuration enforcing failure-inclusive cost accounting.
        """
        eligible = [r for r in results if r.eligible_for_aggregation]
        ineligible_keys = [r.logical_run_key for r in results if not r.eligible_for_aggregation]
        eligible_keys = [r.logical_run_key for r in eligible]

        if not eligible:
            raise ValueError(f"No eligible run results to aggregate for config '{configuration_id}'")

        total_attempts = len(eligible)
        resolved_count = sum(1 for r in eligible if r.resolved)
        failed_count = total_attempts - resolved_count
        pass_rate = round(resolved_count / total_attempts, 4)

        # Failure-Inclusive Cost Accounting Law:
        # Sum cost of ALL attempts (both passing and failing)
        total_cost_dec = sum(Decimal(r.observed_cost_usd) for r in eligible)
        total_cost_usd = f"{total_cost_dec.quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP):.6f}"

        # Cost Per Resolution (CPR):
        # CPR = Total Cost / Resolved Count
        # If resolved_count == 0, CPR is set to 0.000000 (with evidence_sufficient=False) to avoid zero-division
        if resolved_count > 0:
            cpr_dec = (total_cost_dec / Decimal(resolved_count)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            cpr_usd = f"{cpr_dec:.6f}"
        else:
            cpr_usd = "0.000000"

        # Latency statistics
        latencies = sorted([r.latency_ms for r in eligible])
        mean_latency = int(sum(latencies) / len(latencies))
        p95_idx = int(math.ceil(0.95 * len(latencies))) - 1
        p95_latency = latencies[max(0, p95_idx)]

        # Uncertainty intervals
        lower_b, upper_b = calculate_wilson_score_interval(resolved_count, total_attempts)

        quality_floor_breached = pass_rate < quality_floor
        evidence_sufficient = (total_attempts >= 2 and resolved_count > 0 and not quality_floor_breached)

        now_iso = utc_now_rfc3339()
        aggregate_id = generate_aggregate_id({
            "experiment_id": experiment_id,
            "configuration_id": configuration_id,
            "aggregation_policy_version": aggregation_policy_version,
            "eligible_run_keys": eligible_keys,
        })

        return Aggregate(
            schema_version="1.0.0",
            aggregate_id=aggregate_id,
            experiment_id=experiment_id,
            correlation_id=correlation_id,
            configuration_id=configuration_id,
            aggregation_policy_version=aggregation_policy_version,
            eligible_run_keys=eligible_keys,
            ineligible_run_keys=ineligible_keys,
            total_attempts=total_attempts,
            resolved_count=resolved_count,
            failed_count=failed_count,
            pass_rate=pass_rate,
            total_cost_usd=total_cost_usd,
            cpr_usd=cpr_usd,
            mean_latency_ms=mean_latency,
            p95_latency_ms=p95_latency,
            uncertainty_method=UncertaintyMethod.WILSON_SCORE,
            pass_rate_lower_bound=lower_b,
            pass_rate_upper_bound=upper_b,
            evidence_sufficient=evidence_sufficient,
            quality_floor_breached=quality_floor_breached,
            created_at=now_iso,
        )
