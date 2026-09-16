# Course G — Claude Code in Action: hands-on builds

> The author's verification log for course G — read it as a worked example; your own sitting and builds replace these results.

Course G was sat in one go (final quiz 8/8, 11 Sep 2026) with no hands-on during the
sitting. The builds land here afterwards, each paired with the Domain 3 file it belongs
to, per the agreed build map.

| Build | What | Lives at | Pairs with |
|---|---|---|---|
| 2 | `/next-step` slash command + `repo-audit` verification skill | `.claude/commands/next-step.md`, `.claude/skills/repo-audit/SKILL.md` | 3.2 commands and skills |
| 1 | Pre-tool-use hook gate on the exercise 22/23 support agent (structured `is_error`, errorCategory, isRetryable) + a Claude Code `PreToolUse` Bash guard | `practice/exercise-1-support-agent-hardened/`, `.claude/hooks/guard-destructive-bash.sh`, `.claude/settings.json` | G hooks section / 1.4–1.5 |
| 3 | Headless `claude -p` + GitHub Actions review (exercise 2) | `.github/scripts/claude-review.sh`, `.github/review-schema.json`, `.github/workflows/claude-review.yml`, `.claude/commands/review.md` | 3.6 CI/CD |

## Build 2 — placement decisions (the 3.2 table, made concrete)

Two artefacts, deliberately different in every column:

- **`/next-step`** is a *slash command* in the **project's** `.claude/commands/`:
  it is a repeatable ritual anyone with a clone should get (project scope, not
  `~/.claude/`), it loads only when typed (so it costs nothing in other sessions —
  the reason it is not in CLAUDE.md), and it does **not** fork: its output — the next
  step — *is* the deliverable, and its working (one file read) is tiny.
- **`repo-audit`** is a *skill* with **`context: fork`**: its working is large
  (git listings, index cross-checks across the exercises folder) and its conclusion
  is small (three PASS/FAIL lines). Fork protects the **parent** session's window
  from that working; only the report crosses back. `allowed-tools` locks it
  read-only so an audit can never edit while "just looking"; `argument-hint`
  prompts for a scope when invoked bare.

The skill's "Return contract" section is the Domain 2/5 lesson in miniature: define
what crosses the boundary back, not just what the worker does.

## Verification log

- `repo-audit all` invoked live 12 Sep 2026: ran as a **forked** execution, returned
  only the contract-shaped report (3× PASS); the working — `git ls-files` output and
  the 37-row index cross-check — never entered the parent thread. Both artefacts
  registered as invocable the moment their files landed on disk: registration is the
  directory, no config entry anywhere.
- `/next-step` run by the student in a fresh interactive session, 12 Sep 2026: correct
  on all three points (step 19 first unticked; no numbered skips; D/E deliberate).
  Bonus finding: its implication line lagged the live plan — the command reads only
  `progress.md`, and the resequencing note lived elsewhere. Fixed at the source
  (step 19's line now carries the note), not in the command: instance-vs-source.

## Build 3 — exercise 2, the 3.6 file made concrete (13 Sep 2026)

Exercise 2's six items, where each landed and why:

| Item | Artefact | Decision |
|---|---|---|
| 1 | `.claude/CLAUDE.md` (project) + `academy/course-c-claude-api/CLAUDE.md` (directory) | Project file = rules every session pays for; the course-C file = package-shaped conventions that only matter inside that tree. Personal notes stay in `~/.claude/CLAUDE.md`, which CI never sees. |
| 2 | `.claude/rules/tests.md` (`**/tests/**/*.py`, `**/test_*.py`) and `.claude/rules/api.md` (`**/mcp_server.py`, `**/mcp_client.py`, `**/client_loop.py`, `**/pipeline.py`) | File-type conventions across the tree → globs, absent from context until a matching file is touched. |
| 3 | `.claude/commands/review.md` | Human-triggered ritual, project scope; same findings shape as the CI schema. Registered the instant the file landed (the skill list updated live). |
| 4 | `.claude/skills/repo-audit/SKILL.md` | Already built (Build 2): `context: fork`, read-only `allowed-tools`. |
| 5 | `.github/scripts/claude-review.sh` + `review-schema.json` + `workflows/claude-review.yml` | `claude -p --output-format json --json-schema`, read-only `--allowedTools`, budget fuse, incremental review via prior findings. |
| 6 | `.mcp.json` | Already built (exercise 5): `${SUPPORT_DESK_API_KEY}`, `${TOOL_DESCRIPTIONS:-full}`. |

### Verification log (all measured, Claude Code 2.1.148)

- **The hang, reproduced honestly.** Without `-p`: (a) stdin `/dev/null`, stdout a pipe → the CLI detected the non-TTY and printed the answer (no hang); (b) inside a pseudo-TTY (`script -q /dev/null claude …`) → sat 30 s on the **workspace trust dialog** ("Is this a project you created or one you trust? ❯ 1. Yes … Enter to confirm"). That dialog is what `-p` skips (its `--help` text says so). The exam answer is `-p` because detection is version- and runner-dependent; `-p` is deterministic in both cases.
- **Structured output needs two turns.** `--json-schema` with `--max-turns 1` fails with `subtype: error_max_turns`, `stop_reason: tool_use` (the schema is emitted through a tool turn). Without the cap: `structured_output: {"word": "pong", "n": 3}`, `num_turns: 2`. The findings live under `.structured_output`, not `.result`.
- **Run 1 (no prior findings)**, base `fb2e06a` (the exercise 4 diff): 13 turns, $0.97, 6 min 07 s, 10 findings ([run-1-no-prior.json](build-3-review-runs/run-1-no-prior.json), rendered as the PR comment in [run-1-rendered-comment.md](build-3-review-runs/run-1-rendered-comment.md)). Triage: 2 "blockers" were the bot correctly applying an **inaccurate rule** — the first draft of `api.md` said "only the harness retries transients" and named exercise 5's payload shape as the only one, so exercise 4's coordinator-decides design (5.3's own pattern) read as a violation. 1 major misapplied trim-before-append to the synthesis spoke's one-shot request (the payload is not history). 1 minor was wrong (the SDK accepts block objects in `messages`). The other 6 are valid: tautological case-facts check, fence regex that assumes no preamble, `reset()` never called, first-call transient skipped on an empty query, check 2 only inspecting the retry turn, `KeyError` on a bad corpus value. **Lesson:** an always-on rule that misdescribes the codebase turns the reviewer into a false-blocker generator; the fix was the rule, not the code.
- **Run 2 (prior findings = run 1's 10)**, same diff, `api.md` corrected: 13 turns, $1.72 (the prior findings are paid input), 7 findings — 6 marked `unaddressed`, 1 `new` (uncaught `JSONDecodeError` at the spoke boundary), and the **3 resolved by the rule fix were not repeated** ([run-2-with-prior.json](build-3-review-runs/run-2-with-prior.json)). That is 3.6's incremental review working.
- **Comment step, dry-run:** the `jq` template rendered run 1 into the Markdown comment; the `sed` in "Fetch prior findings" recovered all 10 findings from the `<!-- findings: … -->` block — the round-trip the workflow depends on.
- **What CI-style sessions load (asked headless from the repo root):** the project `.claude/CLAUDE.md` and `.claude/rules/` (path-scoped, conditional) — plus, locally only, `~/.claude/CLAUDE.md`, which is the file that will *not* exist on the runner (3.1 + 3.6).
- **First real Actions run (PR `test/claude-review-workflow`, 13 Sep): failed at the review step with `exit code 1` and no message.** The log's `env:` block showed `ANTHROPIC_API_KEY:` with nothing after it — an unset secret arrives as an *empty* variable (a set one prints `***`). Two fixes, both in the script: a pre-flight that exits 2 with the cause named ("ANTHROPIC_API_KEY is empty; add the repository secret"), and `set +e` around the `claude` call so its exit code is captured and its output printed instead of `set -e` aborting inside the command substitution. Measured locally: empty key → exit 2 with the message; an *invalid* key locally still succeeded because the CLI fell back to the keychain login — local auth masks key problems that only CI surfaces (`--bare` would make auth strict but also disables CLAUDE.md discovery, which the review needs, so it is not used). The 2.2 lesson in CI clothing: a bare exit 1 is silent suppression of the cause.
- **LIVE ON GITHUB (PR #1, 13 Sep, after the secret was added): run 1 succeeded** — 3 m 47 s, 14 turns, $0.49, comment posted by `github-actions[bot]` with three findings: (1) *major* — the test commit's message matched neither template in `.claude/CLAUDE.md` (the bot applying the team rule to a commit, correctly; the rule is written for exercise commits, so the human decides whether a fix commit is in scope — rule precision again); (2) *minor* — `import fixtures` duplicating the existing from-import, a genuine nit; (3) *minor, informational* — `reset()` is a no-op while `run()` is called once per process. Comment: <https://github.com/isaac88/claude-certified-architect-foundations-study-guide/pull/1#issuecomment-5652787554>.
- **Run 2 live (merge push, same diff, prior = run 1's comment): success in 41 s, 9 turns, $0.18** — both remaining findings marked `unaddressed`, nothing `new`, the informational note not repeated. The incremental review is cheaper and faster because the bot re-verifies rather than re-discovers.
- **Run 3 live (import fix pushed, prior = run 2's comment): success in 78 s, 11 turns, $0.27** — the duplicate-import finding **disappeared** (resolved, not repeated), the commit-message finding carried as `unaddressed`, and one `new` finding: the fix commit's message also misses the template. Three runs, one PR: discover → re-verify → confirm-resolved, exactly the 3.6 loop.
- **Rule fixed, not commits:** `.claude/CLAUDE.md` named templates only for exercise and step commits, so every fix commit would be flagged forever. Added `<Area>: <what changed>` for everything else. Second time today a bot finding traced to an imprecise always-on rule (after `api.md`): **an always-on rule is a contract the reviewer enforces literally — write it for the whole codebase or it manufactures findings.**

## Build 1 — hooks at both levels (14 Sep 2026)

Two artefacts, one mechanism:

- **SDK level (1.4/1.5):** `practice/exercise-1-support-agent-hardened/agent.py` — `pre_tool_use` gates `process_refund` (identity → ownership → £500 limit) and returns 2.2-shaped denials; `post_tool_use` normalises payloads and books state; the handoff packet is built by the harness from session facts. The system prompt deliberately omits "verify first" so the gate, not the prompt, carries the guarantee.
- **Claude Code level (course G "Hooks"):** `.claude/hooks/guard-destructive-bash.sh` on `PreToolUse` for `Bash`, wired in the committed `.claude/settings.json`. Exit 2 + a reason on stderr = a denial the model can act on — the same shape as `is_error` + `message`.

### Verification log

- Hook script, JSON piped in directly: force-push and hard reset → exit 2 with reasons; `ls -la` → exit 0.
- **Hook live through `claude -p` (2.1.148):** `echo hook-canary` denied — `permission_denials` carries the call and the model quoted the reason verbatim; `echo hook-ok` ran. Registration = file + settings entry, no restart.
- **Agent, two live runs of the same code and prompt:** run 1 — zero gate denials (Haiku verified first and escalated by itself); run 2 — **four denials**, including scenario C attempting the refund *before* `get_customer` (the 1.4 miss, live): denied retryable → verified → retried → denied not-retryable (wrong owner) → escalated. Scenario D (no email): denied → the model asked for the email. 5/5 checks. **The 0-vs-4 variance is the teaching point: that is what "works most of the time" looks like; the gate is what makes it every time.**
- Defect caught by the checks: model-initiated escalation produced a packet with the wrong root cause and no amount → `infer_escalation` now derives both from the session's orders. Facts from the harness, never from the model's prose.
- **False positive one level up:** the first live hook test was blocked by the student's *global* security hook, which matched a destructive-git phrase as text inside a prompt argument (the command would only have reached a dry run). Same lesson as Build 3's rule imprecision. Answer: a harmless canary rule to prove wiring — never a workaround of the guard.
- **Not verified from here before the secret existed:** the Actions run itself. It needs the repository secret `ANTHROPIC_API_KEY` (Settings → Secrets and variables → Actions); the first PR after that is the live test. The six valid exercise 4 findings are left open on purpose — exercise 2 is the review pipeline, not a rework of exercise 4.
