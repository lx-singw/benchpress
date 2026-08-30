"""
FinOps Cost Calculator for Model Runs.
Calculates exact 6-decimal fixed-precision USD costs from token counts and pricing rules.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import Union
from .usage import AccumulatedRunUsage


def calculate_observed_cost(
    usage: AccumulatedRunUsage,
    price_input_per_million_usd: Union[str, Decimal] = "1.250000",
    price_output_per_million_usd: Union[str, Decimal] = "5.000000",
) -> str:
    """
    Calculate observed USD cost with 6-decimal fixed precision string format.
    Formula: (prompt_tokens * price_input / 1M) + (completion_tokens * price_output / 1M)
    """
    p_price = Decimal(str(price_input_per_million_usd))
    c_price = Decimal(str(price_output_per_million_usd))
    one_million = Decimal("1000000")

    input_cost = (Decimal(usage.prompt_tokens) * p_price) / one_million
    # Provider reasoning/thought tokens are incurred output tokens even when
    # they are not returned as visible candidate text.
    output_cost = (Decimal(usage.completion_tokens + usage.reasoning_tokens) * c_price) / one_million
    total_cost = input_cost + output_cost

    quantized = total_cost.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    return f"{quantized:.6f}"
