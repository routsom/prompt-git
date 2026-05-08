#!/usr/bin/env bash
# basic_workflow.sh — demonstrates the core pgit workflow
set -euo pipefail

echo "=== pgit Basic Workflow ==="

# 1. Initialise
pgit init
echo ""

# 2. Create a prompt
cat > prompts/system.md << 'EOF'
You are a helpful customer support agent.
Be polite, concise, and accurate.
If you don't know the answer, say so.
EOF

# 3. Stage and commit
pgit add prompts/system.md
pgit commit -m "initial system prompt"
echo ""

# 4. Modify the prompt
cat > prompts/system.md << 'EOF'
You are a strict customer support agent for TechCorp.
Follow all safety guidelines.
Refuse off-topic questions politely.
Keep responses under 200 tokens.
EOF

# 5. Stage and commit again
pgit add prompts/system.md
pgit commit -m "tightened safety boundaries"
echo ""

# 6. View the log
pgit log
echo ""

# 7. View the diff
pgit diff
echo ""

# 8. Tag a release
pgit tag v1.0 -m "first production release"
echo ""

# 9. Attach eval scores
pgit eval attach pass_rate 0.94
pgit eval attach avg_cost 0.003
echo ""

# 10. View eval scores
pgit eval show
