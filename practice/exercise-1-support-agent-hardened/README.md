# Exercise 1, hardened — support agent with hooks (course G Build 1, step 19)

> ⚠️ **Spoiler — worked solution.** Attempt the brief in [docs/exercises.md](../../docs/exercises.md) first.

Exercise 22/23's agentic loop, unchanged, wrapped with the two lifecycle hooks
from Domain 1.5 and the structured-error contract from 2.2. Spec:
[docs/exercises.md #1](../../docs/exercises.md). Paired Claude Code hook:
[.claude/hooks/guard-destructive-bash.sh](../../.claude/hooks/guard-destructive-bash.sh),
wired in [.claude/settings.json](../../.claude/settings.json).

## Files

| File | What it is |
|---|---|
| [agent.py](agent.py) | Four tools over invented data (`get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`); `pre_tool_use` = the 1.4 prerequisite gate (identity → ownership → £500 limit); `post_tool_use` = identity bookkeeping + payload normalisation (status word, ISO time, internal fields stripped); a harness-built five-field handoff packet; four scenarios and five checks. |
| [run-log.md](run-log.md) | Generated, committed: gate unit demo, checks, per-scenario trace, handoff packets. |

## Run it

```bash
.venv/bin/python practice/exercise-1-support-agent-hardened/agent.py   # claude-haiku-4-5, ~12 calls
```

The API key is read from the environment or the course project's env file, like every other lab here.

## The six brief items, where each lives

1. **Three tools** — `TOOLS` + `ROUTER` (a dict; exercise 23 noted the if/elif router stops scaling at ten).
2. **The loop** — `run_conversation`: exercise 22's six lines, with prints.
3. **Prerequisite gate** — `pre_tool_use`: `process_refund` is denied until a successful `get_customer` has set `session["identity_verified"]`, denied when the order belongs to another customer, denied above `REFUND_LIMIT`. The **system prompt does not say "verify first"** — that is the 1.4 experiment: the gate, not the prompt, carries the guarantee.
4. **PostToolUse** — `post_tool_use`: normalises `lookup_order` (one shape for the model regardless of source, 1.5; five fields not eight, 5.1), records identity, books executed refunds. The over-limit block sits in **Pre**ToolUse, before execution, as 1.5 recommends.
5. **Structured errors** — `error()` builds `{isError, errorCategory, isRetryable, message, attempted}`. The gate returns `permission` + `isRetryable: true` (do the prerequisite, then retry) **and** `permission` + `isRetryable: false` (escalate) — same category, opposite action: the two fields are independent, which is what G3 of the step-14 gap-check asked.
6. **Escalation** — `ESCALATION_CRITERIA` (over limit, wrong owner, customer asks for a human) and `build_handoff`, which assembles the five 1.4 fields from **session state**. When the model escalates on its own initiative, `infer_escalation` derives the root cause and amount from the orders looked up — the packet never depends on the model's prose.

## What the committed run showed (14 Sep 2026)

| Scenario | What the model did | Gate |
|---|---|---|
| A — verified, £120 | `get_customer` + `lookup_order` in parallel, then `process_refund` | allowed; refund executed |
| B — verified, £900 | verified, then **attempted the £900 refund** | denied `permission`/not retryable → model called `escalate_to_human`; packet: over limit, £900 |
| C — verified, someone else's order | **attempted the refund before verifying** (the 1.4 miss, live) → denied retryable → called `get_customer` → retried → denied not-retryable (wrong owner) → escalated | two denials; packet: wrong owner, £45 |
| D — no email given | attempted the refund; denied retryable | model asked for the email and stopped |

Five checks PASS: no refund executed before identity was verified (1 executed, 4 denied); no over-limit refund executed; every denial carried the five 2.2 fields; both handoff packets complete; orders reached the model normalised.

**The finding that matters.** An earlier run of the *same code, same prompt* produced **zero** gate denials: the model verified first and escalated by itself every time. The second run produced four. Neither run is "the" behaviour — that variance is 1.4's "works most of the time", and the gate is what turns it into "every time". Three runs cannot show an 8% miss; the gate does not need to see it to stop it.

**One defect found by the checks and fixed:** when the model escalated before any refund attempt, the first version of the harness recorded "customer asks for a human" and no amount — wrong on both counts. `infer_escalation` now reads the root cause off the session's orders. The packet is built from facts the harness holds, not from what the model said.

## The paired Claude Code hook

`guard-destructive-bash.sh` is the same gate one level up: Claude Code pipes the pending `Bash` call as JSON on stdin; the script denies force-push, hard reset and root-level `rm -rf` with **exit 2 and a reason on stderr** — the model receives the reason, exactly like `is_error` + `message` in `agent.py`. A harmless `hook-canary` rule exists only to prove the wiring without running anything dangerous.

**Measured (Claude Code 2.1.148, headless):** `echo hook-canary` → denied; the session's `permission_denials` lists the call and the model quoted the hook's reason verbatim. `echo hook-ok` → ran. The destructive patterns are unit-tested by piping JSON into the script directly (exit 2 each; `ls -la` exit 0).

**Specimen worth keeping:** the first attempt to test the hook was itself blocked — by the *student's global* security hook, which pattern-matched the text `git push --force` inside a prompt string that would only ever have reached a `--dry-run`. A hook that matches on text produces false positives exactly as an over-broad review rule does (Build 3). The canary rule is the answer: prove the wiring with something harmless, rather than work around the guard.
