#!/usr/bin/env bash
# team_sync.sh — demonstrates push/pull between team members
set -euo pipefail

echo "=== pgit Team Sync ==="

# Set up a "remote" directory
REMOTE_DIR=$(mktemp -d)
echo "Remote: $REMOTE_DIR"

# Alice's repo
mkdir -p /tmp/alice && cd /tmp/alice
pgit init
echo "You are Alice's prompt." > prompt.md
pgit add prompt.md
pgit commit -m "Alice's initial prompt"

# Push to remote
pgit push "$REMOTE_DIR" main
echo ""

# Bob's repo
mkdir -p /tmp/bob && cd /tmp/bob
pgit init
pgit pull "$REMOTE_DIR" main
pgit log

echo ""
echo "=== Both repos are in sync! ==="
