#!/usr/bin/env python3
"""Print the ordered sanitized workflow event timeline for one correlation ID."""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("correlation_id")
    parser.add_argument("--project", required=True)
    parser.add_argument("--dataset", required=True)
    args = parser.parse_args()

    from google.cloud import bigquery

    client = bigquery.Client(project=args.project)
    query = f"""
      SELECT *
      FROM `{args.project}.{args.dataset}.workflow_events`
      WHERE correlation_id = @correlation_id
      ORDER BY timestamp ASC, event_id ASC
    """
    job = client.query(
        query,
        job_config=bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("correlation_id", "STRING", args.correlation_id)
            ]
        ),
    )
    for row in job.result():
        print(json.dumps(dict(row), sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
