# Domain 3 practice exam (8 questions)

Timebox: 16 minutes. Answers at the bottom. Target **7/8**.

---

**1. (3.1)** Developer A’s Claude follows team API naming. Developer B (new) does not. Same repo. Most likely cause?

- A) Instructions in A’s `~/.claude/CLAUDE.md`
- B) B needs a larger model
- C) B has not installed a personal `/review` command
- D) Naming belongs in a skill B forgot to run

**2. (3.1)** You added a testing rule yesterday; this session ignores it. First debugging move?

- A) Rewrite CLAUDE.md in all caps
- B) `/memory` to see which files are loaded
- C) Move everything to `~/.claude/CLAUDE.md`
- D) Disable project CLAUDE.md

**3. (3.2)** `/review` for the whole team after clone, plus a personal verbose brainstorm that must not pollute teammates.

- A) Both in `~/.claude/commands/`
- B) `/review` in `.claude/commands/`; brainstorm skill in `~/.claude/skills/` with `context: fork`
- C) Both in root CLAUDE.md
- D) `/review` in `.claude/config.json` `commands` array

**4. (3.3)** Tests co-located in 50+ directories; same conventions for all. Best mechanism?

- A) `.claude/rules/` with a glob such as `**/*.test.tsx`
- B) CLAUDE.md copied into every directory
- C) One always-on root CLAUDE.md section
- D) A skill developers remember to invoke

**5. (3.4)** Restructure a monolith into microservices (boundaries unknown). First mode?

- A) Direct execution so boundaries emerge
- B) Plan mode
- C) Direct with a complete service map written on day one
- D) Direct now; plan only if you get stuck

**6. (3.4)** Null-pointer in one function, stack trace in hand. Mode?

- A) Plan mode (always, for safety)
- B) Direct execution
- C) Explore subagent only, no edit
- D) Fork the repo and plan for a week

**7. (3.5)** Prose description of a transform; Claude implements a different mapping each run. First technique?

- A) Longer prose
- B) 2–3 concrete input/output examples
- C) Raise temperature
- D) Put the prose in user-level CLAUDE.md

**8. (3.6)** CI: `claude "Analyze this PR"` hangs, waiting for input. Fix?

- A) `-p` / `--print`
- B) Pipe a response script to stdin
- C) 30-second timeout restart loop
- D) `--auto-accept` without changing interactivity

---

## Answers

| # | Answer | Note |
|---|---|---|
| 1 | A | Team law in user-level config |
| 2 | B | `/memory` is the debugger |
| 3 | B | Shared command vs personal forked skill |
| 4 | A | Globs beat 50 directory files |
| 5 | B | Architecture → plan |
| 6 | B | Known local fix → direct |
| 7 | B | Examples beat prose |
| 8 | A | Q10: non-interactive `-p` |

**Score:** ___ / 8

- 7–8: Domain 3 is exam-ready. Do exercise 2.
- 5–6: Re-read the missed task files.
- ≤4: Re-work 3.1, 3.2, and 3.6 — those are pure location/flag questions.
