# Domain 3 — Claude Code Configuration & Workflows (20%)

This domain is configuration. You either know **where the file goes** and **what the flag does**, or you guess. Reasoning will not invent `.claude/commands/`. Hands-on in exercise 2 is not optional.

Same rhythm as Domains 1–2: one file, check questions, next file. Finish with [practice.md](practice.md) (8 questions, target 7/8).

| Task | File | You must know |
|---|---|---|
| 3.1 | [3.1-claude-md.md](3.1-claude-md.md) | User vs project vs directory; `/memory`; `@import` |
| 3.2 | [3.2-commands-and-skills.md](3.2-commands-and-skills.md) | Commands vs skills; `context: fork`; personal vs team paths |
| 3.3 | [3.3-path-specific-rules.md](3.3-path-specific-rules.md) | `.claude/rules/` globs vs directory CLAUDE.md |
| 3.4 | [3.4-plan-mode.md](3.4-plan-mode.md) | Plan vs direct vs Explore vs hybrid |
| 3.5 | [3.5-iterative-refinement.md](3.5-iterative-refinement.md) | Examples > prose; TDD; batch vs sequence |
| 3.6 | [3.6-cicd.md](3.6-cicd.md) | `-p`, JSON schema output, independent review session |

## Scenarios that carry this domain

- Code Generation with Claude Code
- Developer Productivity Tools
- Claude Code for CI/CD

## Three rules that decide most of Domain 3

1. **Team-shared → repo** (`.claude/…`). **Personal → home** (`~/.claude/…`). New hire missing behaviour is almost always user-level config.
2. **Always-on standards → CLAUDE.md / rules.** **On-demand noisy work → skill with `context: fork`.**
3. **CI hangs → `-p`.** Self-review in the generator session is the wrong reviewer.
