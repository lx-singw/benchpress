"""
Pytest Output Parser.
Extracts structured pass/fail assertion counts and test details from test runner output.
"""

import re
from typing import Dict, Any


def parse_pytest_output(stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
    """Parse pytest stdout for assertion counts."""
    passed = 0
    failed = 0
    errors = 0

    # Look for "X passed" pattern
    passed_match = re.search(r"(\d+)\s+passed", stdout)
    if passed_match:
        passed = int(passed_match.group(1))

    # Look for "X failed" pattern
    failed_match = re.search(r"(\d+)\s+failed", stdout)
    if failed_match:
        failed = int(failed_match.group(1))

    # Look for "X error" pattern
    error_match = re.search(r"(\d+)\s+error", stdout)
    if error_match:
        errors = int(error_match.group(1))

    # If exit code is 0 and no specific counts found but tests ran
    if exit_code == 0 and passed == 0 and failed == 0 and errors == 0:
        if "PASSED" in stdout:
            passed = stdout.count("PASSED")

    return {
        "exit_code": exit_code,
        "assertions_passed": passed,
        "assertions_failed": failed + errors,
        "resolved": (exit_code == 0 and failed == 0 and errors == 0 and passed > 0),
        "stdout": stdout,
        "stderr": stderr,
    }
