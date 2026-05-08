"""pgit log — show commit history."""

from __future__ import annotations

import json as json_mod

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()


def log(
    branch: str | None = typer.Option(None, "--branch", help="Branch to show log for."),
    limit: int = typer.Option(20, "--limit", help="Max commits to show."),
    json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show commit history with hashes, messages, timestamps, eval scores."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    commits = repo.log(branch=branch, limit=limit)

    if not commits:
        console.print("[dim]No commits yet.[/dim]")
        return

    if json:
        console.print(json_mod.dumps([c.to_dict() for c in commits], indent=2))
        return

    current_branch = repo.branches.current_branch()
    for c in commits:
        # Build ref decoration
        refs: list[str] = []
        head_hash = repo.branches.resolve_head()
        if c.hash == head_hash:
            if current_branch:
                refs.append(f"HEAD → {current_branch}")
            else:
                refs.append("HEAD")
        ref_str = f"  [yellow]({', '.join(refs)})[/yellow]" if refs else ""

        console.print(
            f"  [bold yellow]{c.hash[:7]}[/bold yellow]{ref_str}  "
            f"{c.message:<40}  [dim]{c.committed_at[:16]}[/dim]"
        )

        if c.eval_scores:
            scores = "  ".join(
                f"{m}: {v}" for m, v in c.eval_scores.items()
            )
            console.print(f"           [cyan]{scores}[/cyan]")
        else:
            console.print("           [dim](no eval scores)[/dim]")
