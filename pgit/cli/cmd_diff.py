"""pgit diff — line diff and semantic diff between commits."""

from __future__ import annotations

import json as json_mod

import typer
from rich.console import Console
from rich.syntax import Syntax

from pgit.diff import line_diff
from pgit.objects import SemanticDiff
from pgit.repo import PromptRepo

console = Console()


def diff(
    from_ref: str | None = typer.Argument(None, help="From ref (default: HEAD~1)."),
    to_ref: str | None = typer.Argument(None, help="To ref (default: HEAD)."),
    semantic: bool = typer.Option(False, "--semantic", help="Show LLM semantic diff."),
    file: str | None = typer.Option(None, "--file", help="Diff a specific file."),
    json: bool = typer.Option(False, "--json", help="Output as JSON."),
) -> None:
    """Show diff between two commits (default: HEAD~1..HEAD)."""
    try:
        repo = PromptRepo.open()
    except FileNotFoundError as e:
        console.print(f"[bold red]✗[/bold red] {e}")
        raise typer.Exit(code=1)

    diffs = repo.diff_texts(from_ref=from_ref, to_ref=to_ref, file_path=file)

    if not diffs:
        console.print("[dim]No changes.[/dim]")
        return

    if semantic:
        from pgit.semantic_diff import generate_semantic_diff

        for path, from_text, to_text in diffs:
            try:
                sd = generate_semantic_diff(from_text, to_text, repo.store)
            except RuntimeError as e:
                console.print(f"[bold red]✗[/bold red] {e}")
                raise typer.Exit(code=1)

            if json:
                console.print(json_mod.dumps(sd.to_dict(), indent=2))
            else:
                _print_semantic_diff(sd, from_ref or "HEAD~1", to_ref or "HEAD")
    else:
        for path, from_text, to_text in diffs:
            diff_text = line_diff(
                from_text, to_text,
                from_label=f"a/{path}",
                to_label=f"b/{path}",
            )
            if json:
                console.print(json_mod.dumps({"path": path, "diff": diff_text}))
            else:
                console.print(f"\n[bold]{path}[/bold]")
                syntax = Syntax(diff_text, "diff", theme="monokai")
                console.print(syntax)


def _print_semantic_diff(sd: SemanticDiff, from_label: str, to_label: str) -> None:
    """Pretty-print a semantic diff."""
    console.print(f"\n  [bold]Semantic diff: {from_label} → {to_label}[/bold]")
    console.print("  " + "─" * 55)
    console.print(f"  [bold]Summary:[/bold]   {sd.summary}")

    if sd.additions:
        console.print(f"\n  [bold green]Added:[/bold green]")
        for a in sd.additions:
            console.print(f"              - {a}")

    if sd.removals:
        console.print(f"\n  [bold red]Removed:[/bold red]")
        for r in sd.removals:
            console.print(f"              - {r}")

    if sd.tone_shift:
        console.print(f"\n  [bold magenta]Tone:[/bold magenta]      {sd.tone_shift}")

    if sd.structural_changes:
        console.print(f"\n  [bold blue]Structure:[/bold blue]")
        for s in sd.structural_changes:
            console.print(f"              - {s}")

    console.print()
