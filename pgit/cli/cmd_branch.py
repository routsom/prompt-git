"""pgit branch — branch management subcommands."""

from __future__ import annotations

import typer
from rich.console import Console

from pgit.repo import PromptRepo

console = Console()

branch_app = typer.Typer(
    name="branch",
    help="Branch management commands.",
    no_args_is_help=True,
    invoke_without_command=True,
)


@branch_app.callback(invoke_without_command=True)
def branch_callback(ctx: typer.Context) -> None:
    """List all branches (default when no subcommand given)."""
    if ctx.invoked_subcommand is None:
        _list_branches()


@branch_app.command("list")
def list_cmd() -> None:
    """List all branches."""
    _list_branches()


def _list_branches() -> None:
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    branches = repo.branches.list_branches()
    current = repo.branches.current_branch()

    if not branches:
        console.print("[dim]No branches yet.[/dim]")
        return

    for name, commit_hash in branches:
        marker = "[bold green]* [/bold green]" if name == current else "  "
        console.print(f"{marker}[bold]{name}[/bold]  [dim]{commit_hash[:7]}[/dim]")


@branch_app.command("create")
def create(
    name: str = typer.Argument(..., help="Branch name."),
    from_ref: str | None = typer.Option(None, "--from", help="Create from commit or branch."),
) -> None:
    """Create a new branch."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    if from_ref:
        commit_hash = repo._resolve_ref(from_ref)
        if commit_hash is None:
            console.print(f"[bold red]✗[/bold red] Cannot resolve '{from_ref}'")
            raise typer.Exit(code=1)
    else:
        commit_hash = repo.branches.resolve_head()
        if commit_hash is None:
            console.print("[bold red]✗[/bold red] No commits yet — commit first.")
            raise typer.Exit(code=1)

    try:
        repo.branches.create_branch(name, commit_hash)
        console.print(
            f"[bold green]✓[/bold green] Created branch [bold]{name}[/bold] "
            f"at [dim]{commit_hash[:7]}[/dim]"
        )
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)


@branch_app.command("switch")
def switch(
    name: str = typer.Argument(..., help="Branch to switch to."),
) -> None:
    """Switch to a branch."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        commit_hash = repo.branches.switch_branch(name)
        console.print(
            f"[bold green]✓[/bold green] Switched to branch [bold]{name}[/bold] "
            f"at [dim]{commit_hash[:7]}[/dim]"
        )
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)


@branch_app.command("delete")
def delete(
    name: str = typer.Argument(..., help="Branch to delete."),
) -> None:
    """Delete a branch (not the commits)."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    try:
        repo.branches.delete_branch(name)
        console.print(f"[bold green]✓[/bold green] Deleted branch [bold]{name}[/bold]")
    except ValueError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)
