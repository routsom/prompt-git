# Contributing to prompt-git

Thank you for your interest in contributing! prompt-git is a community project and we welcome all contributions.

## Getting Started

```bash
git clone https://github.com/your-org/prompt-git
cd prompt-git
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v          # full suite
pytest tests/unit/ -v     # unit only
mypy pgit/ --strict       # type check
ruff check pgit/          # lint
```

All tests must pass and mypy/ruff must be clean before a PR is merged.

## What to Contribute

- **Bug fixes** — open an issue first if non-trivial
- **New prompt format parsers** — see `pgit/parsers/` and `CLAUDE.md` for the protocol
- **New remote backends** — see `pgit/remote.py` and `CLAUDE.md`
- **CLI improvements** — keep output `rich`-formatted and consistent
- **Documentation** — improve examples or the README

## Pull Request Guidelines

1. One PR per logical change
2. Add or update tests for any changed behaviour
3. Run the full test + lint suite before opening
4. Describe *why*, not just *what*, in the PR description
5. Reference any related issue with `Fixes #NNN`

## Reporting Bugs

Use the **Bug Report** issue template. Include:
- `pgit --version` output
- Minimal reproduction steps
- Expected vs actual behaviour

## Code Style

- Python 3.11+ — use modern syntax (`X | Y`, `match`, etc.)
- `ruff` for formatting and linting (config in `pyproject.toml`)
- `mypy --strict` must pass — no `type: ignore` without justification
- Keep functions small and focused
- No web UI — CLI only

## Commit Messages

Follow conventional commits loosely:
```
feat: add YAML turns parser
fix: handle empty index in commit
docs: improve semantic diff example
```

## License

By contributing you agree your changes will be licensed under the [MIT License](LICENSE).
