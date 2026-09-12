# Course G — Claude Code in Action: hands-on builds

Course G was sat in one go (final quiz 8/8, 11 Sep 2026) with no hands-on during the
sitting. The builds land here afterwards, each paired with the Domain 3 file it belongs
to, per the agreed build map.

| Build | What | Lives at | Pairs with |
|---|---|---|---|
| 2 | `/next-step` slash command + `repo-audit` verification skill | `.claude/commands/next-step.md`, `.claude/skills/repo-audit/SKILL.md` | 3.2 commands and skills |
| 1 | Pre-tool-use hook gate on the exercise 22/23 support agent (structured `is_error`, errorCategory, isRetryable) | pending — step 19 | G hooks section |
| 3 | Headless `claude -p` + GitHub Actions review (exercise 2) | pending — step 22, after 3.6 | 3.6 CI/CD |

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

- `/next-step` run in a fresh session: _pending — see check below_
- `repo-audit` invoked and observed to fork (working absent from main thread): _pending_
