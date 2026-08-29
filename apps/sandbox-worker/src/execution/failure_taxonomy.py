"""
Failure Taxonomy Classifier.
Classifies execution failures into standard FailureReason enum categories.
"""

from typing import Optional
from contracts.states import FailureReason


def classify_run_failure(
    exit_code: int,
    assertions_failed: int,
    timed_out: bool = False,
    turn_limit_exceeded: bool = False,
    security_breach: bool = False,
    infra_error: Optional[str] = None,
) -> FailureReason:
    """Classify execution outcome into sovereign FailureReason."""
    if timed_out:
        return FailureReason.TIMEOUT
    if turn_limit_exceeded:
        return FailureReason.MAX_TURNS_EXCEEDED
    if security_breach:
        return FailureReason.RUNTIME_EXCEPTION
    if infra_error:
        return FailureReason.INFRASTRUCTURE_ERROR
    if assertions_failed > 0 or exit_code != 0:
        return FailureReason.ORACLE_ASSERTION_FAILED
    return FailureReason.NONE
