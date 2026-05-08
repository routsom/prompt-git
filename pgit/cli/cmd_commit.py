"""pgit commit — create a commit from staged files."""

from __future__ import annotations

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()


def commit(
    message: str = typer.Option(..., "-m", "--message", help="Commit message."),
    author: str | None = typer.Option(None, "--author", help="Override commit author."),
) -> None:
    """Create a commit from the staged index."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        c = repo.commit(message=message, author=author)
        console.print(
            f"[bold green]✓[/bold green] [{c.hash[:7]}] {c.message}"
        )
        console.print(f"  [dim]author: {c.author} | {c.committed_at}[/dim]")
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)
