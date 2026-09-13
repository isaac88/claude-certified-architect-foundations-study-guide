---
description: Review changes against the team standards and path rules; findings only, no edits
allowed-tools: Read, Grep, Glob, Bash(git diff:*), Bash(git status:*), Bash(git log:*)
argument-hint: [base-ref]
---

Review the changes as an independent reviewer who did not write them.

Scope: if `$ARGUMENTS` names a ref, review `git diff $ARGUMENTS...HEAD`; otherwise
review the working tree (`git diff HEAD` plus untracked files from `git status`).

Apply, in this order: `.claude/CLAUDE.md`, any `.claude/rules/*.md` whose `paths`
match a changed file, and the folder's own `CLAUDE.md` if one exists. Read a changed
file in full before commenting on it.

Report only findings, most severe first, one line each:

`<file>:<line> — <blocker|major|minor> — <rule violated> — <what to change>`

Then one closing line: how many findings, and whether the change is mergeable as is.
Do not restate the diff, do not praise, do not edit anything. The CI job runs this
same review headless via `.github/scripts/claude-review.sh`.
