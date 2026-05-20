"""pgit add — stage prompt files for commit."""

from __future__ import annotations

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()


def add(
    files: list[str] = typer.Argument(..., help="Prompt files to stage."),
    model: str | None = typer.Option(None, "--model", help="Model hint for staged files."),
) -> None:
    """Stage prompt files for commit."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    for f in files:
        try:
            blob = repo.add(f, model_hint=model)
            console.print(
                f"  [green]staged[/green] {f} → [dim]{blob.hash[:8]}[/dim] "
                f"[dim]({blob.format})[/dim]"
            )
        except FileNotFoundError:
            console.print(f"  [red]error[/red] file not found: {f}")
