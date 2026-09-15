#!/usr/bin/env bash
# Claude Code PreToolUse hook (course G "Hooks", Domain 1.5 one level up).
# Claude Code pipes the pending tool call as JSON on stdin; exit 2 DENIES it
# and the stderr text is what the model sees as the reason. Exit 0 allows.
# Same shape as agent.py's pre_tool_use: deterministic, runs every time,
# returns a reason the model can act on.
set -euo pipefail
# FAIL CLOSED. Claude Code treats exit 2 as "deny" and any OTHER non-zero exit
# as "the hook broke" — it shows the error to the human and lets the call run.
# So an internal failure here (jq missing, malformed stdin) must become exit 2,
# or a broken guard silently opens the door. (Gap-check 5c, 15 Sep 2026.)
trap 'echo "PreToolUse guard: internal failure — denying by default. Fix the hook, then retry." >&2; exit 2' ERR
deny() { echo "PreToolUse guard: denied — $1. Ask the human to run this by hand." >&2; exit 2; }
input="$(cat)"
# Claude Code always sends the pending call as JSON. No payload means the
# contract is broken; a broken contract denies (fail closed), it does not allow.
[[ -n "$input" ]] || deny "no tool payload received on stdin"
cmd="$(jq -r '.tool_input.command // ""' <<<"$input")"
case "$cmd" in
  *"hook-canary"*)                               deny "canary rule — harmless, exists only to prove this hook is wired" ;;
  *"git push"*"--force"*|*"git push -f"*)        deny "force-push rewrites shared history" ;;
  *"git reset --hard"*)                          deny "hard reset discards uncommitted work" ;;
  *"rm -rf /"*|*"rm -rf ~"*|*"rm -rf ."*)        deny "recursive delete of a root, home or the project" ;;
esac
exit 0
