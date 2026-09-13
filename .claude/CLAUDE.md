# Team standards — claude-certified-architect-foundations-study-guide

Every rule here is paid for in every request. Task procedures live in `.claude/commands/` and `.claude/skills/`; file-type rules live in `.claude/rules/`.

- British English in notes, comments and commit messages.
- One Python environment: `.venv/` at the repo root, run everything as `.venv/bin/python <path>` from the root. The only exceptions are the two course projects that ship their own lock (see `academy/course-c-claude-api/CLAUDE.md`).
- Secrets live in `academy/course-c-claude-api/.env` only. Never write a key into a source file, a log, or a commit.
- Never commit `HANDOFF.md`, `.env*`, `*.pdf`, or course download assets — `.gitignore` already lists them; do not weaken it.
- One commit per working exercise, message `Add <where> exercise NN: <what it is>` or `Pass step NN: <what>`; push after each.
- Scripts that call the API print progress per step; a silent three-minute run is a bug.
- An exercise covers exactly its brief. Extra findings go in a `reference/` folder next to it, not in the exercise.
- `progress.md` is the source of truth for the study plan; fix plan drift there, never in a command or note that merely reads it.
- Numbers in synthetic fixtures (`practice/exercise-4-research-pipeline/fixtures.py`) are invented; never quote them as facts.
