"""pgit eval — eval score management subcommands."""

from __future__ import annotations

import json as json_mod

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()

eval_app = typer.Typer(name="eval", help="Eval score management.", no_args_is_help=True)


@eval_app.command("attach")
def attach(
    metric: str = typer.Argument(..., help="Metric name."),
    value: float = typer.Argument(..., help="Score value."),
    commit: str | None = typer.Option(None, "--commit"),
    notes: str | None = typer.Option(None, "--notes"),
) -> None:
    """Attach an eval score to a commit."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)
    if commit is None:
        commit = repo.branches.resolve_head()
    if commit is None:
        console.print("[bold red]✗[/bold red] No commits yet.")
        raise typer.Exit(code=1)
    try:
        repo.evals.attach(commit, metric, value, notes)
        console.print(f"[bold green]✓[/bold green] Attached {metric}={value} to [dim]{commit[:7]}[/dim]")
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)


@eval_app.command("show")
def show(
    commit: str | None = typer.Option(None, "--commit"),
    json: bool = typer.Option(False, "--json"),
) -> None:
    """Show all eval scores for a commit."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)
    if commit is None:
        commit = repo.branches.resolve_head()
    if commit is None:
        console.print("[bold red]✗[/bold red] No commits yet.")
        raise typer.Exit(code=1)
    scores = repo.evals.get_scores(commit)
    if not scores:
        console.print(f"[dim]No eval scores for {commit[:7]}.[/dim]")
        return
    if json:
        console.print(json_mod.dumps([s.to_dict() for s in scores], indent=2))
        return
    console.print(f"[bold]Eval scores for {commit[:7]}:[/bold]\n")
    for s in scores:
        notes_str = f"  [dim]({s.notes})[/dim]" if s.notes else ""
        console.print(f"  [cyan]{s.metric}[/cyan]: {s.value}{notes_str}")
