---
name: repo-audit
description: Verify this study repo's consistency before a commit or at the start of a sitting — gitignore hygiene, course exercise index vs files on disk, progress.md ordering. Use when asked to audit, verify, or health-check the repo.
context: fork
allowed-tools: Read, Grep, Glob, Bash(git ls-files:*), Bash(git status:*), Bash(git check-ignore:*)
argument-hint: [hygiene|index|progress|all]
---

Run the audit scoped by the argument (`all` if none given). The working is large —
you will read many files — but the parent thread needs only the verdicts.

## Checks

**hygiene** — files that must never be tracked. Run `git ls-files` and confirm none of
these appear: `HANDOFF.md`, any `.env*` (except `.env.example`), any `*.pdf`, anything
under `academy/course-c-claude-api/exercises/images/`, `tests/fixtures/`. Also run
`git status --porcelain` and flag any of those sitting staged.

**index** — the exercise index in `academy/course-c-claude-api/README.md` must match
the numbered exercise files actually on disk under
`academy/course-c-claude-api/exercises/`. Report rows without files and files without
rows. Gitignored course assets do not count as missing.

**progress** — in `progress.md`, every tick must be internally consistent: no step both
ticked and containing an unresolved `___ / N` score blank; flag any ticked step whose
line references a commit or date that is absent.

## Return contract

Return ONLY a report of this shape — never the file listings or grep output themselves:

```
repo-audit: PASS | FAIL
- hygiene: PASS | FAIL — <one line of evidence>
- index: PASS | FAIL — <one line: counts, and names only for mismatches>
- progress: PASS | FAIL — <one line>
```

If a check fails, name the offending path(s) — nothing else crosses back.
