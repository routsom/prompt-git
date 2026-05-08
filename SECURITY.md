# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Instead, report them privately via [GitHub Security Advisories](../../security/advisories/new) or email the maintainers directly (see the GitHub profile).

We will acknowledge receipt within 48 hours and aim to release a fix within 14 days for confirmed issues.

## Scope

- **In scope:** Secrets leaking from the `.promptgit/` store, path traversal in `pgit add`, SQLite injection via untrusted input, insecure remote sync
- **Out of scope:** Vulnerabilities in dependencies (report upstream), issues requiring physical access

## API Key Handling

`PGIT_LLM_KEY` is read from the environment and passed directly to the Anthropic SDK. It is never written to `.promptgit/store.db` or logged. Always use environment variables — never hard-code API keys in prompt files.
