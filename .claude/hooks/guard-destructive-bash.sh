#!/usr/bin/env bash
# Claude Code PreToolUse hook (course G "Hooks", Domain 1.5 one level up).
# Claude Code pipes the pending tool call as JSON on stdin; exit 2 DENIES it
# and the stderr text is what the model sees as the reason. Exit 0 allows.
# Same shape as agent.py's pre_tool_use: deterministic, runs every time,
# returns a reason the model can act on.
set -euo pipefail
cmd="$(jq -r '.tool_input.command // ""')"
deny() { echo "PreToolUse guard: denied — $1. Ask the human to run this by hand." >&2; exit 2; }
case "$cmd" in
  *"hook-canary"*)                               deny "canary rule — harmless, exists only to prove this hook is wired" ;;
  *"git push"*"--force"*|*"git push -f"*)        deny "force-push rewrites shared history" ;;
  *"git reset --hard"*)                          deny "hard reset discards uncommitted work" ;;
  *"rm -rf /"*|*"rm -rf ~"*|*"rm -rf ."*)        deny "recursive delete of a root, home or the project" ;;
esac
exit 0
