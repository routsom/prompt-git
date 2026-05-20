"""pgit pull — pull from a remote."""

from __future__ import annotations

import os

import typer
from rich.console import Console

from pgit.remote import LocalRemote
from pgit.repo import PromptRepo

console = Console()


def pull(
    remote: str | None = typer.Argument(None, help="Remote URL or path."),
    branch: str | None = typer.Argument(None, help="Branch to pull."),
) -> None:
    """Pull from a configured remote."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    remote_url = remote or os.environ.get("PGIT_REMOTE_URL")
    if not remote_url:
        console.print(
            "[bold red]✗[/bold red] No remote specified. Pass a path or set PGIT_REMOTE_URL."
        )
        raise typer.Exit(code=1)

    branch_name = branch or repo.branches.current_branch() or "main"
    r = LocalRemote(remote_url)
    count = r.pull(repo.store, branch_name)
    console.print(f"[bold green]✓[/bold green] Pulled {count} objects from {remote_url}")
