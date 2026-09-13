# Course G — Claude Code in Action: hands-on builds

Course G was sat in one go (final quiz 8/8, 11 Sep 2026) with no hands-on during the
sitting. The builds land here afterwards, each paired with the Domain 3 file it belongs
to, per the agreed build map.

| Build | What | Lives at | Pairs with |
|---|---|---|---|
| 2 | `/next-step` slash command + `repo-audit` verification skill | `.claude/commands/next-step.md`, `.claude/skills/repo-audit/SKILL.md` | 3.2 commands and skills |
| 1 | Pre-tool-use hook gate on the exercise 22/23 support agent (structured `is_error`, errorCategory, isRetryable) | pending — step 19 | G hooks section |
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
- **Not verified from here:** the Actions run itself. It needs the repository secret `ANTHROPIC_API_KEY` (Settings → Secrets and variables → Actions); the first PR after that is the live test. The six valid exercise 4 findings are left open on purpose — exercise 2 is the review pipeline, not a rework of exercise 4.
