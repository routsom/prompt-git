"""pgit merge — merge a branch into the current branch."""

from __future__ import annotations

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()


def merge(
    branch: str = typer.Argument(..., help="Branch to merge."),
    if_better: str | None = typer.Option(
        None, "--if-better", help="Only merge if eval metric is better."
    ),
    min_improvement: float = typer.Option(5.0, "--min-improvement", help="Minimum improvement %%."),
) -> None:
    """Merge a branch into the current branch."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        c = repo.merge(branch, if_better=if_better, min_improvement=min_improvement)
        console.print(
            f"[bold green]✓[/bold green] [{c.hash[:7]}] {c.message}"
        )
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)
