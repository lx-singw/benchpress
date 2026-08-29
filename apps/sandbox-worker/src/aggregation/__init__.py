"""
Aggregation & Early Stopping Package.
"""

from .aggregator import ConfigurationAggregator, calculate_wilson_score_interval
from .early_stopping import EarlyStoppingEvaluator, StopAction, StopEvaluationResult
from .sufficiency import SufficiencyEvaluator

__all__ = [
    "ConfigurationAggregator",
    "calculate_wilson_score_interval",
    "EarlyStoppingEvaluator",
    "StopAction",
    "StopEvaluationResult",
    "SufficiencyEvaluator",
]
