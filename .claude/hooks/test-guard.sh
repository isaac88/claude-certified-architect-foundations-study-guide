#!/usr/bin/env bash
# Unit test for guard-destructive-bash.sh: pipes pending-call JSON into the hook
# the way Claude Code does and asserts the exit code. Run from anywhere:
#   .claude/hooks/test-guard.sh
# Kept as a file so the test strings never appear in an interactive command —
# the guard applies to the sessions that test it.
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
GUARD="$HERE/guard-destructive-bash.sh"
fail=0

check() {  # check <expected-exit> <label> <stdin-json>
  local expected="$1" label="$2" payload="$3" actual
  printf '%s' "$payload" | "$GUARD" >/dev/null 2>"$HERE/.last-stderr"; actual=$?
  if [[ "$actual" == "$expected" ]]; then
    echo "PASS  exit $actual  $label"
  else
    echo "FAIL  exit $actual (expected $expected)  $label"; fail=1
  fi
  [[ -s "$HERE/.last-stderr" ]] && sed 's/^/        stderr: /' "$HERE/.last-stderr"
  rm -f "$HERE/.last-stderr"
}

check 0 "benign command allowed"            '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'
check 2 "canary denied"                     '{"tool_name":"Bash","tool_input":{"command":"echo hook-canary"}}'
check 2 "force-push denied"                 '{"tool_name":"Bash","tool_input":{"command":"git push --force origin main"}}'
check 2 "hard reset denied"                 '{"tool_name":"Bash","tool_input":{"command":"git reset --hard HEAD~1"}}'
check 2 "malformed stdin -> fail CLOSED"    'not json at all'
check 2 "empty stdin -> fail CLOSED"        ''

exit $fail
