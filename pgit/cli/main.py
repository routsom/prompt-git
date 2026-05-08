"""Typer entry point — the pgit CLI."""

from __future__ import annotations

import typer

from pgit.cli.cmd_add import add
from pgit.cli.cmd_branch import branch_app
from pgit.cli.cmd_commit import commit
from pgit.cli.cmd_diff import diff
from pgit.cli.cmd_eval import eval_app
from pgit.cli.cmd_init import init
from pgit.cli.cmd_log import log
from pgit.cli.cmd_merge import merge
from pgit.cli.cmd_pull import pull
from pgit.cli.cmd_push import push
from pgit.cli.cmd_status import status
from pgit.cli.cmd_tag import tag

app = typer.Typer(
    name="pgit",
    help="Git-style version control for LLM prompts.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

app.command()(init)
app.command()(add)
app.command()(commit)
app.command()(log)
app.command()(diff)
app.command()(merge)
app.command()(tag)
app.command()(status)
app.command()(push)
app.command()(pull)
app.add_typer(branch_app, name="branch")
app.add_typer(eval_app, name="eval")


def app_entry() -> None:
    """Entry point for the pgit CLI."""
    app()
