"""pgit tag — tag a commit."""

from __future__ import annotations

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()


def tag(
    name: str = typer.Argument(..., help="Tag name."),
    commit: str | None = typer.Argument(None, help="Commit to tag (default: HEAD)."),
    message: str | None = typer.Option(None, "-m", "--message", help="Tag message."),
) -> None:
    """Tag a commit. Defaults to HEAD."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        t = repo.tag(name=name, commit_hash=commit, message=message)
        console.print(
            f"[bold green]✓[/bold green] Tagged [bold]{t.name}[/bold] → "
            f"[dim]{t.target[:7]}[/dim]"
        )
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)
