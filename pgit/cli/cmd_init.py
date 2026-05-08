"""pgit init — initialise a new prompt repository."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()


def init() -> None:
    """Initialise a new prompt repository in the current directory."""
    try:
        repo = PromptRepo.init(Path.cwd())
        console.print(
            f"[bold green]✓[/bold green] Initialised prompt repo at "
            f"[cyan]{repo.pgit_dir}[/cyan]"
        )
    except FileExistsError:
        console.print("[bold red]✗[/bold red] Prompt repo already initialised here.")
        raise typer.Exit(code=1)
