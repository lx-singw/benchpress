"""
Rich-Colorized Command-Line Interface (CLI) for Benchpress.
"""

import sys
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
from .client import SyncBenchpressClient
from .exceptions import BenchpressError

console = Console()


@click.group()
@click.version_option(version="1.0.0", prog_name="benchpress")
def main():
    """Benchpress: The Economic Intelligence & Dynamic Model Router Platform for AI Agents."""
    pass


@main.command()
@click.option("--task", "-t", default="code_bug_fix", type=click.Choice(["code_bug_fix", "architectural_refactor", "financial_extraction", "quick_edit"]), help="Task complexity type")
@click.option("--lang", "-l", default="python", type=click.Choice(["python", "typescript", "rust", "go", "java"]), help="Codebase language")
@click.option("--model", "-m", default="claude-3-7-sonnet", help="Current frontier model to benchmark against")
@click.option("--budget", "-b", default=0.50, type=float, help="Max budget ceiling in USD")
@click.option("--url", default="http://localhost:3000", help="Benchpress API base URL")
def route(task, lang, model, budget, url):
    """Query real-time dynamic model routing recommendation."""
    client = SyncBenchpressClient(base_url=url)
    try:
        with console.status(f"[cyan]Evaluating Pareto frontier for {task} ({lang}) vs {model}..."):
            res = client.get_routing_recommendation(
                task_type=task,
                codebase_language=lang,
                current_model=model,
                max_budget_per_task_usd=budget,
            )

        rec = res.recommendation

        # Build Rich Rationale Panel
        panel_content = (
            f"[bold green]Strategy:[/bold green] {rec.recommendedStrategy}\n"
            f"[bold cyan]Choreography:[/bold cyan] {rec.plannerModel} (Planner) + {rec.coderModel} (Coder)\n"
            f"[bold yellow]Projected CPR:[/bold yellow] ${rec.projectedCprUsd:.3f} / task (vs ${rec.currentModelCprUsd:.3f} on {model})\n"
            f"[bold magenta]Cost Reduction:[/bold magenta] [bold underline]{rec.projectedSavingsPct}% Savings[/bold underline]\n"
            f"[bold white]Pass@1 Estimate:[/bold white] {rec.passAt1EstimatePct}%\n\n"
            f"[dim italic]Rationale: {rec.rationale}[/dim italic]"
        )

        console.print(Panel(panel_content, title="[bold #00F0FF]Benchpress Routing Recommendation[/bold #00F0FF]", border_style="#00F0FF"))

    except BenchpressError as e:
        console.print(f"[bold red]API Error:[/bold red] {e.message}", file=sys.stderr)
    except Exception as e:
        console.print(f"[bold red]Error connecting to Benchpress:[/bold red] {str(e)}", file=sys.stderr)


@main.command()
@click.option("--suite", "-s", default="swe_bench_verified", help="Benchmark suite name")
@click.option("--url", default="http://localhost:3000", help="Benchpress API base URL")
def leaderboard(suite, url):
    """View continuous economic leaderboard table."""
    client = SyncBenchpressClient(base_url=url)
    try:
        res = client.list_benchmarks(suite=suite)

        table = Table(title=f"Benchpress Economic Leaderboard: {suite.upper()}", header_style="bold #00F0FF")
        table.add_column("Rank", style="dim")
        table.add_column("Model Name", style="bold white")
        table.add_column("Provider", style="cyan")
        table.add_column("CPR ($)", style="bold green", justify="right")
        table.add_column("Pass@1 (%)", style="yellow", justify="right")
        table.add_column("Mean Turns", style="magenta", justify="right")
        table.add_column("Pareto", style="bold green", justify="center")

        for idx, row in enumerate(res.data):
            pareto_str = "[bold green]YES[/bold green]" if row.paretoFrontier else "[dim]NO[/dim]"
            table.add_row(
                f"#{idx + 1}",
                row.modelName,
                row.provider,
                f"${row.cprUsd:.3f}",
                f"{row.passRatePct:.1f}%",
                f"{row.meanTurns:.1f}",
                pareto_str,
            )

        console.print(table)

    except Exception as e:
        console.print(f"[bold red]Failed to fetch leaderboard:[/bold red] {str(e)}", file=sys.stderr)


@main.command()
@click.option("--task-id", "-t", required=True, help="Task ID (e.g. django__django-11099)")
@click.option("--suite", "-s", default="SWE_BENCH_VERIFIED", help="Benchmark task suite")
@click.option("--model", "-m", default="hybrid-gemini-pro-flash", help="Model ID")
@click.option("--url", default="http://localhost:3000", help="Benchpress API base URL")
def run(task_id, suite, model, url):
    """Dispatch evaluation trajectory run."""
    client = SyncBenchpressClient(base_url=url)
    try:
        with console.status(f"[cyan]Dispatching trajectory for {task_id} on {model}..."):
            res = client.dispatch_trajectory(task_suite=suite, task_id=task_id, model_id=model)

        console.print(f"[bold green]✓ Trajectory Queued:[/bold green] {res.trajectoryId}")
        console.print(f"  [dim]Task: {res.taskSuite} / {res.taskId}[/dim]")
        console.print(f"  [dim]Model: {res.modelId}[/dim]")
        console.print(f"  [dim]Budget Cap: ${res.budgetLimitUsd:.2f}[/dim]")

    except Exception as e:
        console.print(f"[bold red]Failed to dispatch trajectory:[/bold red] {str(e)}", file=sys.stderr)


if __name__ == "__main__":
    main()
