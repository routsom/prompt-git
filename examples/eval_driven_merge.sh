#!/usr/bin/env bash
# eval_driven_merge.sh — demonstrates --if-better merge gating
set -euo pipefail

echo "=== pgit Eval-Driven Merge ==="

pgit init
echo "You are a helpful assistant." > system.md
pgit add system.md
pgit commit -m "baseline prompt"
pgit eval attach pass_rate 0.85

# Create experiment branch
pgit branch create experiment/gpt4o
pgit branch switch experiment/gpt4o

echo "You are an expert assistant. Be precise and thorough." > system.md
pgit add system.md
pgit commit -m "experiment: more precise tone"
pgit eval attach pass_rate 0.92

# Switch back and try merge
pgit branch switch main

# This will succeed — 0.92 > 0.85 (8.2% improvement > 5% threshold)
pgit merge experiment/gpt4o --if-better pass_rate
echo ""

pgit log
