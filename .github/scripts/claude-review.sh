#!/usr/bin/env bash
# Headless Claude Code review — exercise 2 item 5 (Domain 3.6).
#
# Usage: .github/scripts/claude-review.sh <base-ref> [prior-findings.json] > review.json
#
# Prints the full `claude -p --output-format json` envelope; the findings are
# under `.structured_output` (enforced by review-schema.json). Exits non-zero
# when Claude reports an error, so the CI step fails loudly instead of posting
# an empty comment.
#
# Why each flag is here:
#   -p                      non-interactive. Without it a job that has a TTY
#                           opens the interactive UI and waits for input forever;
#                           one that has no TTY happens to fall back to print
#                           mode on current versions. -p makes it deterministic.
#   --output-format json    one machine-parseable result, not free text.
#   --json-schema           enforces the findings shape (no regex on prose).
#   --allowedTools          read-only: a reviewer that can edit is not a reviewer.
#   --no-session-persistence CI has no next turn to resume.
#   --max-budget-usd        the fuse; a runaway review must cost cents, not dollars.
#   < /dev/null             CI gives no stdin; without this the CLI waits 3s for
#                           piped input and warns (measured).
# Note: structured output needs at least two turns; do NOT add --max-turns 1
# (measured: error_max_turns with stop_reason tool_use).
set -euo pipefail

BASE="${1:?usage: claude-review.sh <base-ref> [prior-findings.json]}"
PRIOR="${2:-}"

# Fail with a named cause, not a bare exit 1. In Actions an unset secret
# arrives as an EMPTY variable (the log shows `ANTHROPIC_API_KEY:` with no
# `***`), and claude then exits 1 with nothing on stderr.
if [[ -z "${ANTHROPIC_API_KEY:-}" ]]; then
  echo "claude-review: ANTHROPIC_API_KEY is empty. Add the repository secret (Settings → Secrets and variables → Actions) and re-run." >&2
  exit 2
fi
for tool in claude jq git; do
  command -v "$tool" >/dev/null || { echo "claude-review: $tool not on PATH" >&2; exit 2; }
done
HERE="$(cd "$(dirname "$0")" && pwd)"
SCHEMA="$(cat "$HERE/../review-schema.json")"

PRIOR_BLOCK=""
if [[ -n "$PRIOR" && -s "$PRIOR" ]]; then
  # Incremental review (3.6): the bot repeating itself is how teams stop reading it.
  PRIOR_BLOCK="PRIOR FINDINGS from the previous run, as JSON:
$(cat "$PRIOR")
Report ONLY findings that are new, or previously reported and still present (status \"unaddressed\"). Never repeat a finding that the current code has resolved."
fi

PROMPT="You are an independent reviewer: you did not write these changes and you have no memory of why they were made.
Review the diff \`git diff ${BASE}...HEAD\` (run it; read any changed file in full before commenting on it).
Apply .claude/CLAUDE.md, every .claude/rules/*.md whose paths match a changed file, and the folder's own CLAUDE.md if present.
Report only findings, most severe first, with the exact file and line. Do not restate the diff. Do not edit anything.
${PRIOR_BLOCK}"

echo "claude-review: base=${BASE} prior=${PRIOR:-none} model=${CLAUDE_REVIEW_MODEL:-sonnet}" >&2
set +e   # capture claude's exit code instead of letting set -e swallow it silently
OUT="$(claude -p "$PROMPT" \
  --output-format json \
  --json-schema "$SCHEMA" \
  --model "${CLAUDE_REVIEW_MODEL:-sonnet}" \
  --allowedTools "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*)" \
  --no-session-persistence \
  --max-budget-usd "${CLAUDE_REVIEW_BUDGET_USD:-2}" < /dev/null)"
CODE=$?
set -e

printf '%s\n' "$OUT"
if [[ $CODE -ne 0 ]]; then
  echo "claude-review: claude exited ${CODE}. Output (first 2000 chars): ${OUT:0:2000}" >&2
  exit "$CODE"
fi
if [[ "$(printf '%s' "$OUT" | jq -r '.is_error // false')" == "true" ]]; then
  echo "claude-review: Claude reported an error: $(printf '%s' "$OUT" | jq -c '.errors // .subtype')" >&2
  exit 1
fi
echo "claude-review: $(printf '%s' "$OUT" | jq -r '.structured_output.findings | length') finding(s), cost \$$(printf '%s' "$OUT" | jq -r '.total_cost_usd')" >&2
