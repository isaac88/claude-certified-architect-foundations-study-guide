#!/usr/bin/env bash
# Raw HTTP against the Messages API — no SDK.
#
# WHAT THIS TEACHES
#     The wire shape. Everything the SDK does is this request. Reading it
#     raw is closer to what the exam tests than SDK sugar: one endpoint,
#     `content` as a list of blocks, `stop_reason` as the loop signal.
#
# EXAM LINK (Domain 1)
#     Look at `stop_reason` and the `content` array in the response. That
#     array is why the 1.1 premature-stop bug exists.
#
# RUN — option A, Console API key (needs ANTHROPIC_API_KEY set or in .env)
#     bash reference/raw-http.sh
#
# RUN — option B, Console OAuth (needs `ant auth login --profile study` first)
#     USE_OAUTH=1 bash reference/raw-http.sh
#     USE_OAUTH=1 ANT_PROFILE=study bash reference/raw-http.sh
#
# NOTE: a Claude Pro/Max/Team/Enterprise subscription is NOT a valid
# credential here. See the README — Console billing is separate.

set -euo pipefail

[ -f "$(dirname "$0")/../.env" ] && set -a && . "$(dirname "$0")/../.env" && set +a

if [ "${USE_OAUTH:-0}" = "1" ]; then
  command -v ant >/dev/null || {
    echo "ant CLI not on PATH. It is installed via mise.toml — cd to the repo root" >&2
    echo "so mise activates, or run: mise install github:anthropics/anthropic-cli" >&2
    exit 1
  }
  # Captured by substitution on purpose: the token must never be echoed to a
  # terminal, a log, or an agent transcript.
  PROFILE_ARGS=()
  [ -n "${ANT_PROFILE:-}" ] && PROFILE_ARGS=(--profile "$ANT_PROFILE")
  if ! TOKEN="$(ant "${PROFILE_ARGS[@]+"${PROFILE_ARGS[@]}"}" auth print-credentials --access-token 2>/dev/null)" || [ -z "$TOKEN" ]; then
    echo "No Console OAuth credential for profile '${ANT_PROFILE:-default}'." >&2
    echo "Run: ant auth login --profile ${ANT_PROFILE:-study}" >&2
    echo "Sign in with a PERSONAL email — an employer-managed domain may be" >&2
    echo "blocked from creating Console orgs, and a Team subscription is not a" >&2
    echo "Console credential either. See the README." >&2
    exit 1
  fi
  AUTH_HEADERS=(-H "Authorization: Bearer ${TOKEN}" -H "anthropic-beta: oauth-2025-04-20")
else
  : "${ANTHROPIC_API_KEY:?set ANTHROPIC_API_KEY in academy/course-c-claude-api/.env}"
  AUTH_HEADERS=(-H "x-api-key: ${ANTHROPIC_API_KEY}")
fi

# -w writes the HTTP status on its own last line so we can branch on it.
# Without this, curl exits 0 on a 401/429/500 and the script "succeeds"
# while the caller gets an error body. That is Domain 5.3 — error
# propagation — happening in three lines of shell.
RESPONSE="$(curl -sS -w $'\n%{http_code}' https://api.anthropic.com/v1/messages \
  "${AUTH_HEADERS[@]}" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-5",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "In two sentences, what is an agentic loop?"}
    ]
  }')"

STATUS="$(printf '%s' "$RESPONSE" | tail -n1)"
BODY="$(printf '%s' "$RESPONSE" | sed '$d')"

printf '%s' "$BODY" | python3 -m json.tool
echo "HTTP $STATUS"

case "$STATUS" in
  2*) ;;                                    # fine
  401) echo "Bad or missing credential — see the README." >&2; exit 1 ;;
  429) echo "Rate limited. Check the retry-after header." >&2; exit 1 ;;
  4*)  echo "Request rejected — read error.type in the body above." >&2; exit 1 ;;
  5*)  echo "Server error — retryable." >&2; exit 1 ;;
  *)   echo "Unexpected status." >&2; exit 1 ;;
esac

# The response you are reading for:
#
#   {
#     "id": "msg_...",
#     "type": "message",
#     "role": "assistant",
#     "content": [ {"type": "text", "text": "..."} ],   <- a LIST
#     "stop_reason": "end_turn",                        <- the loop signal
#     "usage": {"input_tokens": N, "output_tokens": N}
#   }
#
# With tools declared, `content` can hold a "text" block AND a "tool_use"
# block in the same message, and `stop_reason` becomes "tool_use". That is
# the whole of the 1.1 lesson, visible on the wire.
