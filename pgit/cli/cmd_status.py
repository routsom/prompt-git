"""pgit status — show staged and unstaged changes."""

from __future__ import annotations

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()


def status() -> None:
    """Show staged and unstaged changes."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    st = repo.status()

    branch = st["branch"] or "(detached HEAD)"
    head = st["head"] or "(no commits)"
    console.print(f"On branch [bold]{branch}[/bold]  [dim]{head}[/dim]\n")

    if st["staged"]:
        console.print("[bold green]Staged changes:[/bold green]")
        for path, blob_hash in st["staged"]:
            console.print(f"  [green]new file:[/green]   {path}  [dim]({blob_hash})[/dim]")
        console.print()

    if st["unstaged"]:
        console.print("[bold red]Unstaged changes:[/bold red]")
        for path in st["unstaged"]:
            console.print(f"  [red]modified:[/red]   {path}")
        console.print()

    if not st["staged"] and not st["unstaged"]:
        console.print("[dim]Nothing to commit, working tree clean.[/dim]")
