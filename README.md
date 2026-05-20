# prompt-git (`pgit`)

**Git for your prompts. Commit, diff, branch, merge, and rollback LLM prompts — with semantic diffs that tell you what *meaning* changed.**

[![CI](https://github.com/routsom/prompt-git/actions/workflows/ci.yml/badge.svg)](https://github.com/routsom/prompt-git/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/sr-prompt-git)](https://pypi.org/project/sr-prompt-git/)
[![Python](https://img.shields.io/pypi/pyversions/sr-prompt-git)](https://pypi.org/project/sr-prompt-git/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The problem

Prompts are **load-bearing infrastructure** in production AI systems — but they're managed like config files: no history, no diffs, no rollback.

When your agent regresses at 2 AM, you have no idea:
- Which prompt changed?
- What exactly changed in it?
- Was it broken before, or did a recent edit introduce the regression?

## The solution

```
$ pgit diff HEAD~1 --semantic

  Semantic diff: 7b1e4f1 → a3f9c2d
  ───────────────────────────────────────────────────────────
  Summary:   Tone shifted from permissive to strict; added hard
             limits on off-topic queries.

  Added:     - Explicit instruction to refuse off-topic questions
             - Hard word limit of 200 tokens per response
             - Escalation path for complex queries

  Removed:   - "Feel free to explore" phrasing
             - Open-ended example in the few-shot section

  Tone:      Permissive → Strict / Professional
```

`pgit` gives prompts the same rigorous version control that code has had for 30 years — plus one thing code diffs can't do: describe what the **meaning** changed.

---

## Install

```bash
pip install sr-prompt-git

# For semantic diff (requires Anthropic API key):
pip install sr-prompt-git[semantic]
export PGIT_LLM_KEY=sk-ant-...
```

---

## Quick start

```bash
# 1. Initialise a prompt repo in your project
pgit init

# 2. Stage and commit your first prompt
echo "You are a helpful assistant. Be concise." > system.md
pgit add system.md
pgit commit -m "initial system prompt"

# 3. Attach your eval scores to the commit
pgit eval attach pass_rate 0.87
pgit eval attach avg_cost_usd 0.003

# 4. Experiment on a branch
pgit branch create experiment/stricter
pgit branch switch experiment/stricter

echo "You are a strict assistant. Refuse all off-topic queries." > system.md
pgit add system.md
pgit commit -m "tightened safety boundaries"
pgit eval attach pass_rate 0.94

# 5. See what semantically changed
pgit diff HEAD~1 --semantic

# 6. Merge back — only if pass_rate improved by 5%+
pgit branch switch main
pgit merge experiment/stricter --if-better pass_rate
#  ✓ Merged: pass_rate 0.87 → 0.94 (+8.0%)
```

---

## Why prompt-git?

| Pain point | pgit solution |
|---|---|
| "Which prompt caused the regression?" | `pgit log` — full history with eval scores per commit |
| "What exactly changed between these versions?" | `pgit diff v1.2 v1.3 --semantic` |
| "Roll back to last week's prompt" | `pgit tag` + `pgit branch switch` |
| "Only ship if it tested better" | `pgit merge --if-better pass_rate` |
| "Audit all prompt changes this sprint" | `pgit log --limit 50 --json` |

---

## Full CLI reference

```
pgit init                                      Initialise a prompt repo
pgit add <file> [--model <hint>]               Stage files for commit
pgit commit -m <msg> [--author <name>]         Commit staged files
pgit status                                    Show staged / unstaged state
pgit log [--branch <b>] [--limit N] [--json]  Commit history with eval scores
pgit diff [<from>] [<to>] [--semantic]         Line diff or LLM semantic diff
pgit branch list                               List branches
pgit branch create <name> [--from <ref>]       Create a branch
pgit branch switch <name>                      Switch branches
pgit branch delete <name>                      Delete a branch
pgit merge <branch> [--if-better <metric>]     Merge (optionally gated on eval)
pgit tag <name> [<commit>] [-m <msg>]          Tag a commit
pgit eval attach <metric> <value>              Attach eval score to HEAD
pgit eval show [--commit <hash>] [--json]      Show eval scores
pgit push [<remote>] [<branch>]                Push to remote
pgit pull [<remote>] [<branch>]                Pull from remote
```

`<from>` / `<to>` accept: commit hashes, branch names, tag names, `HEAD`, `HEAD~N`.

---

## Supported prompt formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| Plaintext | `.txt`, `.md` | Standard text / markdown prompts |
| Jinja2 | `.j2`, `.jinja`, `.jinja2` | Template prompts with variables |
| JSON Messages | `.json` | OpenAI-style `[{role, content}]` arrays |
| YAML Turns | `.yaml`, `.yml` | Multi-turn prompt files |

---

## How it works

Everything lives in `.promptgit/store.db` — a plain SQLite file you can open with any viewer.

Objects are **content-addressed** (SHA-256, like git):

- **Blob** — immutable prompt text; identical content stored once regardless of commits
- **Tree** — maps file paths → blob hashes
- **Commit** — tree + parent + message + author + timestamp; immutable once written
- **Tag** — named pointer to a commit
- **SemanticDiff** — LLM-generated meaning diff, cached permanently by `(from_hash, to_hash)`

Eval scores live in a separate table linked by commit hash — so attaching scores never changes a commit's hash.

---

## Semantic diff

```bash
pgit diff HEAD~1 --semantic            # all changed prompts, HEAD~1..HEAD
pgit diff v1.0 v2.0 --semantic --file system.md   # one file, specific tags
pgit diff --semantic --json            # machine-readable JSON output
```

- Powered by `claude-haiku-4-5-20251001` by default (fast, cheap)
- Override model: `PGIT_LLM_MODEL=claude-sonnet-4-6`
- Results are **cached permanently** — same pair of versions never hits the LLM twice
- Always **opt-in** via `--semantic` — never called automatically

---

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `PGIT_LLM_KEY` | required for `--semantic` | Anthropic API key |
| `PGIT_LLM_MODEL` | `claude-haiku-4-5-20251001` | Model for semantic diff |
| `PGIT_AUTHOR` | `git config user.name` | Default commit author |
| `PGIT_DB` | `.promptgit/store.db` | Override store path |
| `PGIT_REMOTE_URL` | — | Default remote URL |

---

## TypeScript SDK

A read-only TypeScript SDK is included for teams reading prompt history from Node.js:

```typescript
import { PromptRepo } from 'prompt-git'

const repo = PromptRepo.open('/path/to/project')
const commits = repo.log({ limit: 10 })
console.log(commits[0].message)
```

---

## Examples

See the [`examples/`](examples/) directory:

- [`basic_workflow.sh`](examples/basic_workflow.sh) — init → add → commit → diff
- [`team_sync.sh`](examples/team_sync.sh) — push/pull with a shared remote
- [`eval_driven_merge.sh`](examples/eval_driven_merge.sh) — eval-gated merges in CI

---

## Development

```bash
git clone https://github.com/your-org/prompt-git
cd prompt-git
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

pytest tests/ -v        # run tests
mypy pgit/ --strict     # type check
ruff check pgit/        # lint
```

Tests use cassette recordings — no live LLM calls in CI.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). New parsers, remote backends, bug fixes, and docs all welcome.

## License

[MIT](LICENSE) © prompt-git contributors
