# Getting started — make this journey yours

Welcome! 👋 This repo is a complete, self-contained study path for the **Claude Certified Architect (Foundations)** exam — built by one candidate, designed to be forked by the next. Everything you need is committed; everything personal is not.

## 🚀 Make this repo yours

1. **Fork** (or clone) the repo.
2. **Blank the tracker** — the committed `progress.md` is the original author's journey. Replace it with the template:

   ```bash
   cp progress.template.md progress.md
   ```

3. **Start your weak-spots ledger** — it stays local (gitignored) and fills up with *your* misses:

   ```bash
   cp progress/weak-spots-template.md progress/weak-spots.md
   ```

4. Optionally clear or keep the author's run logs (`practice/exercise-*/run-log.md`, `academy/course-g-claude-code/README.md`) — they are worked examples, useful to compare against once you have attempted a build yourself.

## 🧭 Which file do I follow?

Three planning files, one job each:

1. **[roadmap.md](roadmap.md)** — *follow this one*, day by day. It pairs each Academy course section with the domain file it feeds.
2. **[study-steps.md](study-steps.md)** — owns the canonical numbering 1–30 that `progress.md` ticks. You read it once; the roadmap sequences it for you.
3. **[study-plan.md](study-plan.md)** — only the calendar estimate (4-week and 2-week paths). It never overrides the roadmap.

So: roadmap tells you *what today*, progress.md records *where you are*, study-plan.md guesses *how long*.

## 📖 The study method

The files teach the content; this ritual is what made it stick. Run it with your own Claude session acting as instructor.

- **One sitting = one course section + one domain file.** Never a course section alone — the course teaches the vendor's happy path; the domain files teach the decisions and traps the exam tests.
- **Check questions are answered in chat, and marked.** Ask your Claude session to act as the instructor: it asks the task file's check questions, you answer with a letter **and a why**, and a pass requires a why that kills all three distractors — the right letter alone is a half.
- **Practice sets are gates, not milestones.** Sit them in chat with the options reshuffled (so you cannot anchor on remembered positions). Below target means re-read the missed files before moving on.
- **Gap-check after every build.** After each hands-on exercise, have the session probe the concepts the build was meant to prove. Answering by being taught does not count as a pass — only a cold, unprompted answer does.
- **Every fail or half goes in the ledger.** Add a row to your `progress/weak-spots.md` with where it showed, a status (OPEN/QUEUED/VERIFY/CLOSED) and how to recheck it cold. Step 30 of the plan is driven entirely by this file.
- **Keep a local `HANDOFF.md`** (gitignored) as your per-sitting handoff note — where you stopped, what the next sitting opens with. It is rewritten every sitting; the ledger is the durable record.

## ⚙️ Setup

- **Tooling:** [mise.toml](../mise.toml) pins Python 3.12 and the Anthropic `ant` CLI — run `mise install` (note: mise's registry shortname `ant` is Apache Ant; use `mise install github:anthropics/anthropic-cli`).
- **One Python environment** at the repo root:

  ```bash
  python3 -m venv .venv
  .venv/bin/pip install -r academy/course-c-claude-api/requirements.txt
  ```

  Run everything as `.venv/bin/python <path>` from the root. The only exceptions are the two course projects that ship their own `uv.lock` (`academy/course-c-claude-api/mcp-project/` and `claude-code-project/`) — see [../academy/course-c-claude-api/CLAUDE.md](../academy/course-c-claude-api/CLAUDE.md).
- **Secrets:** copy `academy/course-c-claude-api/.env.example` to `.env` in that folder and fill it in. That `.env` is the only place a key lives — never in a source file or a commit. Variables you may need beyond `ANTHROPIC_API_KEY`: `CLAUDE_MODEL` (the mcp-project asserts it at startup), `VOYAGE_API_KEY` (exercise 28 only), and `SUPPORT_DESK_API_KEY` / `TOOL_DESCRIPTIONS` (interpolated by the root `.mcp.json` for the exercise 5 lab).

## 🔒 What a fresh clone will not have

Deliberately gitignored — each absence is explained in [.gitignore](../.gitignore):

- `HANDOFF.md` — the author's per-sitting handoff note. Yours will be different; keep it local.
- `progress/weak-spots.md` — the live ledger. Create yours from the template (step 3 above).
- The official exam-guide PDF — download it yourself from Anthropic Academy.
- Course download assets (lesson images, CSVs, `claude-code-project/tests/fixtures/`) — re-download pointers live in the gitignore comments and [.claude/rules/tests.md](../.claude/rules/tests.md).

## ⚠️ Spoilers — read this before opening `practice/`

- `practice/exercise-*/` folders are the author's **worked solutions** to the five briefs in [exercises.md](exercises.md). Attempt each brief yourself first; open the solution afterwards to compare.
- Each domain's `practice.md` has the answer key at the bottom. Sit the set in chat with options reshuffled instead of reading the file top to bottom.

---

That's it — fork it, blank the tracker, and start at Phase A of the [roadmap](roadmap.md). Good luck! 🎓
