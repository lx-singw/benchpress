#!/usr/bin/env python3
"""
Benchpress Cross-Platform Cloud Deployment CLI (`cloud_cli.py`).
Provides 1-click execution for deploy, bootstrap, secrets, smoke test, teardown, and env sync
across Windows, macOS, and Linux.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

DEFAULT_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "benchpress-platform")
DEFAULT_REGION = os.environ.get("GOOGLE_CLOUD_REGION", "us-central1")


def get_bash_executable() -> str:
    """Resolve cross-platform bash executable."""
    if sys.platform == "win32":
        git_bash = Path("C:/Program Files/Git/bin/bash.exe")
        if git_bash.exists():
            return str(git_bash)
        git_bash_x86 = Path("C:/Program Files (x86)/Git/bin/bash.exe")
        if git_bash_x86.exists():
            return str(git_bash_x86)
    return "bash"


def run_script(script_name: str, args: list) -> int:
    """Execute a bash automation script."""
    bash_exec = get_bash_executable()
    script_path = Path("scripts") / script_name
    if not script_path.exists():
        print(f"❌ Error: Script {script_path} not found.")
        return 1

    cmd = [bash_exec, str(script_path)] + args
    return subprocess.call(cmd)


def main():
    parser = argparse.ArgumentParser(
        description="Benchpress 1-Click Unified Cloud Deployment & Infrastructure CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/cloud_cli.py deploy --env dev
  python scripts/cloud_cli.py deploy --env prod --project-id my-gcp-project
  python scripts/cloud_cli.py smoke --env dev
  python scripts/cloud_cli.py teardown --env dev
        """,
    )

    subparsers = parser.add_subparsers(dest="command", required=True, help="Cloud command to run")

    # Command: deploy
    deploy_p = subparsers.add_parser("deploy", help="Deploy infrastructure and containers (dev vs prod)")
    deploy_p.add_argument("--env", choices=["dev", "prod"], default="dev", help="Target environment")
    deploy_p.add_argument("--project-id", default=DEFAULT_PROJECT, help="GCP Project ID")
    deploy_p.add_argument("--region", default=DEFAULT_REGION, help="GCP Region")
    deploy_p.add_argument("--skip-terraform", action="store_true", help="Skip Terraform apply")
    deploy_p.add_argument("--skip-docker", action="store_true", help="Skip Docker build/push")
    deploy_p.add_argument("--skip-smoke", action="store_true", help="Skip post-deployment smoke test")

    # Command: bootstrap
    boot_p = subparsers.add_parser("bootstrap", help="Enable 9 GCP APIs and configure Docker auth")
    boot_p.add_argument("--project-id", default=DEFAULT_PROJECT, help="GCP Project ID")
    boot_p.add_argument("--region", default=DEFAULT_REGION, help="GCP Region")

    # Command: secrets
    sec_p = subparsers.add_parser("secrets", help="Provision Secret Manager keys (dev vs prod)")
    sec_p.add_argument("--env", choices=["dev", "prod"], default="dev", help="Target environment")
    sec_p.add_argument("--project-id", default=DEFAULT_PROJECT, help="GCP Project ID")
    sec_p.add_argument("--gemini-api-key", help="Google Gemini API Key")

    # Command: smoke
    smoke_p = subparsers.add_parser("smoke", help="Run automated live cloud smoke test")
    smoke_p.add_argument("--env", choices=["dev", "prod"], default="dev", help="Target environment")
    smoke_p.add_argument("--project-id", default=DEFAULT_PROJECT, help="GCP Project ID")
    smoke_p.add_argument("--region", default=DEFAULT_REGION, help="GCP Region")
    smoke_p.add_argument("--web-url", help="Custom Web URL to test")

    # Command: teardown
    tear_p = subparsers.add_parser("teardown", help="Safe targeted environment teardown")
    tear_p.add_argument("--env", choices=["dev", "prod"], default="dev", help="Target environment")
    tear_p.add_argument("--project-id", default=DEFAULT_PROJECT, help="GCP Project ID")
    tear_p.add_argument("--region", default=DEFAULT_REGION, help="GCP Region")
    tear_p.add_argument("--force", "-f", action="store_true", help="Skip confirmation prompt")

    # Command: env
    env_p = subparsers.add_parser("env", help="Sync cloud parameters to .env.cloud")
    env_p.add_argument("--env", choices=["dev", "prod"], default="dev", help="Target environment")
    env_p.add_argument("--project-id", default=DEFAULT_PROJECT, help="GCP Project ID")
    env_p.add_argument("--region", default=DEFAULT_REGION, help="GCP Region")

    parsed, unknown = parser.parse_known_args()

    args_list = []
    for k, v in vars(parsed).items():
        if k == "command" or v is None or v is False:
            continue
        if v is True:
            args_list.append(f"--{k.replace('_', '-')}")
        else:
            args_list.extend([f"--{k.replace('_', '-')}", str(v)])

    args_list.extend(unknown)

    script_map = {
        "deploy": "gcp_deploy_all.sh",
        "bootstrap": "gcp_bootstrap.sh",
        "secrets": "gcp_setup_secrets.sh",
        "smoke": "gcp_smoke_test.sh",
        "teardown": "gcp_teardown.sh",
        "env": "setup_cloud_env.sh",
    }

    script_name = script_map[parsed.command]
    return run_script(script_name, args_list)


if __name__ == "__main__":
    sys.exit(main())
