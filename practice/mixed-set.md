# Mixed practice set (12 questions)

Cross-domain, exam tempo. 24 minutes. Answers at the bottom.

Covers the six official scenario types. Original items — not copied from Anthropic’s sample PDF.

---

**1. Support.** Identity verification is skipped on 12% of refunds. Which change actually closes the hole?

- A) System prompt emphasis on `get_customer` first
- B) Few-shot of the correct sequence
- C) Programmatic prerequisite blocking `lookup_order` / `process_refund` until a verified customer ID exists
- D) Classifier that removes refund tools from billing-unrelated chats

**2. Support.** Both tools have one-line descriptions; order questions hit `get_customer`. First step?

- A) Few-shot routing
- B) Expand descriptions (formats, examples, boundaries)
- C) Keyword pre-router
- D) Merge tools

**3. Support.** Over-escalates password resets; under-escalates policy gaps. Calibrate with:

- A) Confidence threshold 70%
- B) Explicit criteria + few-shot of escalate vs resolve
- C) Put escalate last and shorten its description
- D) Sentiment threshold

**4. Claude Code.** Shared `/review` command. Path?

- A) `~/.claude/commands/`
- B) `.claude/commands/` in the project
- C) CLAUDE.md
- D) `.claude/config.json`

**5. Claude Code.** Monolith split, many files, unknown boundaries.

- A) Plan mode first
- B) Direct execution so boundaries emerge
- C) Direct with a complete service map written in advance
- D) Direct now, plan if it hurts

**6. Claude Code.** TS / Python / Terraform conventions by file type.

- A) `.claude/rules/` globs
- B) One labelled CLAUDE.md
- C) Only folder CLAUDE.md files
- D) Runtime env toggles

**7. Research.** “Impact of AI on creative industries” report is visual-arts only. All spokes succeeded.

- A) Synthesis window too small
- B) Coordinator decomposition too narrow
- C) Search queries biased
- D) Report template

**8. Research.** Search spoke times out. Coordinator should receive:

- A) Structured error (type, attempts, partials, alternatives)
- B) Generic unavailable after hidden retries
- C) Empty success
- D) Uncaught exception that aborts the job

**9. Research.** Synthesis needs to check a claim. Tooling?

- A) Scoped `verify_fact` tool
- B) Round-trip every claim through the coordinator to search
- C) Full web-search toolset on synthesis
- D) Trust research spokes to have pre-verified everything

**10. CI.** Job hangs for input.

- A) `-p`
- B) Stdin script
- C) Kill after 30s
- D) `--auto-accept` only

**11. CI.** Batches API for PR review *and* nightly audit?

- A) Batch nightly only; sync PR review
- B) Batch both
- C) Sync both
- D) Batch PRs; sync nightly

**12. Extraction.** Guarantee JSON shape.

- A) “Output as JSON”
- B) `tool_use` + schema + `tool_choice`
- C) Regex
- D) Assume prose is parseable

---

## Answers

| # | Ans | Domain | Rule |
|---|---|---|---|
| 1 | C | 1.4 | Money → gate, not prompt |
| 2 | B | 2.1 | Descriptions first |
| 3 | B | 5.2 | Criteria + few-shot; not sentiment/confidence |
| 4 | B | 3.2 | Project commands directory |
| 5 | A | 3.4 | Architecture → plan mode |
| 6 | A | 3.3 | Glob rules |
| 7 | B | 1.2 | Narrow decomposition |
| 8 | A | 5.3 / 2.2 | Structured errors |
| 9 | A | 1.3 / 2.3 | Scoped tools |
| 10 | A | 3.6 | Headless `-p` |
| 11 | A | 4.5 | Batch non-blocking only |
| 12 | B | 4.3 | Schema via tool_use |

**Score:** ___ / 12

Map misses back to the task file. Re-sit Domain 1 practice if 7, 1, or 9 are wrong — those are the 27% domain.
