#!/usr/bin/env python3
"""Deprecated synthetic evidence generator.

The previous implementation wrote hard-coded records into ``evidence/`` and
described them as measured production proof. That path is intentionally
disabled. Use the fixture manifest for UI/schema samples. A live exporter and
offline verifier are implemented under WP-12 of BP-PLAN-007 before any new
artifact may be called evidence.
"""

from __future__ import annotations


def main() -> int:
    print(
        "Evidence generation is disabled: hard-coded examples are DEMO_FIXTURE "
        "and cannot be promoted to measured evidence."
    )
    print(
        "See docs/planning/07-g0-remediation-implementation-plan.md, WP-12, "
        "for the required live exporter and verifier."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
