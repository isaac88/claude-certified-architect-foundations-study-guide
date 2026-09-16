# Progress tracker

Follow **[docs/roadmap.md](docs/roadmap.md)** for what to do next; it maps onto the numbered steps in **[docs/study-steps.md](docs/study-steps.md)**. Tick here as you complete each step.

## Phase 0 — Orientation

- [x] 1. Registered on Anthropic Academy
- [x] 2. Read `docs/exam-overview.md`
- [x] 3. Read `docs/exam-strategy.md`
- [x] 4. Read `docs/scenarios.md`
- [x] 5. Read `cheatsheets/decision-rules.md`

Official practice exam score: ____  
Exam date: ________

## Official Academy courses (in progress)

Source: Anthropic Academy → Prepare for this exam. Details: [docs/academy-courses.md](docs/academy-courses.md).

- [x] A. AI Fluency: Framework & Foundations (100) — optional if already fluent
- [x] B. Claude 101 (100) — done 30 Aug 2026
- [x] C. Building with the Claude API (100–200) — **COMPLETE 8 Sep 2026: final assessment 23/23 (100%)**. Every quiz 100% (tool use, Features 7/7, MCP 6/6, Claude Code 7/7). 45 exercises coded: [academy/course-c-claude-api](academy/course-c-claude-api/)
- [ ] D. Claude with Amazon Bedrock (100–200) — only if you use Bedrock
- [ ] E. Claude on Google Cloud (100–200) — only if you use GCP
- [x] F. Introduction to Model Context Protocol (200) — done 10 Sep 2026, final quiz **7/7**; content was already covered by course C ex. 38–44 + exercise 5 lab
- [x] G. Claude Code in Action (200) — done 11 Sep 2026, final quiz **8/8** (seventh consecutive perfect quiz); whole course sat in one go. Hands-on builds (hooks, commands, headless) still land in the repo paired with Domain 3 files

## Phase 1 — Domain 1 (27%)

- [x] 6. 1.1 Agentic loops + premature-stop answers — 31 Aug 2026
- [x] 7. 1.2 Multi-agent orchestration — 1 Sep 2026
- [x] 8. 1.3 Subagent invocation — 1 Sep 2026
- [x] 9. 1.4 Workflow enforcement — 2 Sep 2026
- [x] 10. 1.5 SDK hooks — 2 Sep 2026
- [x] 11. 1.6 Task decomposition — 3 Sep 2026
- [x] 12. 1.7 Session state — 3 Sep 2026
- [x] 13. Domain 1 practice: 10 / 10 (target 8+) — 3 Sep 2026, options reshuffled in chat, no anchoring
- [x] 14. Exercise 1 — support agent with real loop — 8 Sep 2026, credited against course C ex. 22-23 (loop, router, multi-tool, is_error results all built + gap-checked); gate/hooks/structured-error fields deferred to step 19 (Exercise 1 hardened)

## Phase 2 — Domain 2 then Domain 5

- [x] 15. Domain 2 files 2.1–2.5 — 9 Sep 2026 (2.1–2.2 on 7–8 Sep; 2.3–2.5 in one sitting, 9 Sep)
- [x] 16. Domain 2 practice: **7 / 7** (target 6+) — 9 Sep 2026, options reshuffled, +3/3 on retest items (payload ×2, return contract). Exercise 5 done 10 Sep 2026: [practice/exercise-5-tool-contract-lab](practice/exercise-5-tool-contract-lab/) — 3-tool MCP server + client loop, 4 error categories verified live, `[]` vs permission proven, `tool_choice` forcing measured, `.mcp.json` with `${ENV_VAR}`; routing misroute did NOT reproduce (names+schemas rescued it — see log conclusions)
- [x] 17. Domain 5 files 5.1–5.6 — 11 Sep 2026 (5.1–5.2 on 10 Sep; 5.3–5.6 in one sitting, 11 Sep)
- [x] 18. Domain 5 practice: **6 / 6** (target 5+) — 11 Sep 2026, options reshuffled; +4/5 on retest items (caching ×4, trigger design). One residual: the "long gap → don't cache at all" trap resurfaced once (burst caching is always on; the gap only decides which write you re-pay)
- [x] 19. Exercise 1 hardened **or** exercise 4 started — both done: exercise 4 on 13 Sep; Exercise 1 hardened = course G Build 1 on 14 Sep 2026, [practice/exercise-1-support-agent-hardened](practice/exercise-1-support-agent-hardened/): PreToolUse gate (identity → ownership → £500) + PostToolUse normalisation on the ex-22/23 loop, 2.2 errors, harness-built handoff; 4 live denials, 5/5 checks; paired Claude Code Bash guard hook verified live. Gap-check pending

## Phase 3 — Domain 3 then Domain 4

- [x] 20. Domain 3 files 3.1–3.6 — 12 Sep 2026 (3.1 on 11 Sep; 3.2–3.6 in one sitting, 12 Sep, alongside Build 2 — the biggest single-day span yet)
- [x] 21. Domain 3 practice: **8 / 8** (target 7+) — 13 Sep 2026, options reshuffled. Retests: path-right-reason-differs, always-enforced-vs-always-loaded, batches-vs-per-PR all clean; fork-direction credited on the final letter but the first instinct was the inversion — retest cold again at step 28
- [x] 22. Exercise 2 — Claude Code team workflow — 13 Sep 2026, with course G Build 3: project + directory CLAUDE.md, `.claude/rules/` (tests, api), `/review`, `claude -p` review script + schema + GitHub Actions workflow; hang reproduced (trust dialog under a PTY), incremental review verified live (3 resolved findings not repeated). Actions run itself awaits the `ANTHROPIC_API_KEY` repo secret — see [academy/course-g-claude-code/README.md](academy/course-g-claude-code/README.md)
- [x] 23. Domain 4 files 4.1–4.6 — 15 Sep 2026 (4.1–4.2 in the late-night sitting; 4.3–4.6 in one sitting later the same day). All six bonus MCQs correct; from 4.4 on, every why properly sized with full distractor autopsies — the undersized-why habit did not fire once in 4.4–4.6
- [x] 24. Domain 4 practice: **8 / 8** (target 7+) — 15 Sep 2026, same sitting as 4.3–4.6, options reshuffled; +5/5 on retest items with whys: eval bands (the ledger's expected-fail row) passed with the resolution mechanism unprompted; score-vs-delta, ship-vs-noise and `content[0].text`-with-thinking closed; Haiku 4096 minimum right letter but why undersized — one probe outstanding
- [x] 25. Exercise 3 — extraction pipeline — 16 Sep 2026, [practice/exercise-3-extraction-pipeline](practice/exercise-3-extraction-pipeline/): 10 invented documents in 10 layouts, 11 scored fields against gold, 8/8 measured checks. Headlines: "respond only with JSON" parsed strictly **0/10** (well-formed JSON, always inside a ```json fence) against 20/20 on a forced tool; few-shot took the layouts its examples covered 97.0% → **100%** and the layouts they did not cover **97.4% → 97.4%**; the blank PO box returned `None` (nullable), the string `'null'` (required non-nullable) and `''` (retry under a wrong validator rule); Batches 10/10 in 185.6s at 96.4% — the 1.8-point gap to the sync arm is the retry loop a batch request cannot run. Gap-check 16 Sep: all five items **TAUGHT at the student's request, not attempted** — five cold items booked at step 28 (see `progress/weak-spots.md` — the live ledger, local and gitignored; newcomers create theirs from [progress/weak-spots-template.md](progress/weak-spots-template.md))

## Phase 4 — Lock together

- [x] 26. Exercise 4 finished (research pipeline) — built and verified live 13 Sep 2026 (6/6 measured checks): [practice/exercise-4-research-pipeline](practice/exercise-4-research-pipeline/). Gap-check 13 Sep: Q1 half+FAIL (empty-vs-error inverted in timeout costume — said ok+`[]` triggers a retry; it's the do-not-retry signal), Q2–4 answered by teaching at the student's request, not passed. Step 28 mixed set MUST retest cold: empty-vs-error in timeout costume, trim-per-consumer, deterministic provenance join, dedup ownership (source_id). Same day, in the session that built the lab, all four were attempted unprompted: Q3 and Q4 passed, Q1 and Q2 half — retest queue unchanged
- [x] 27. Decision rules from memory — 16 Sep 2026, closed book, six rounds over every cheatsheet section (52 items): **41 clean, 9 half, 2 fail**. Rounds 5-6 (prompts/output, context/reliability) were 16/17 — recall is not the gap. Both fails and most halves were *second halves*: fork **direction** (inverted again), a broken Claude Code hook **fails open** (answered about the deny path), the where-without-why fix, fork's two properties, the layer in the `allowedTools` answer. A seventh scenario round (no row labels) then showed the live pattern: a correctly-behaving spoke was blamed for the coordinator's `end_turn`, and a perfect class-imbalance diagnosis arrived with no remedy attached
- [ ] 28. Mixed set: ___ / **16** (target 13+) — raised from 12 on 16 Sep 2026 because the ledger's booked cold-retest queue had outgrown a 12-item set; items are drawn from that queue (the two cold fails first), sat in four blocks of four at exam tempo, letters deliberately alternated against anchoring
- [ ] 29. Official Academy practice exam
- [ ] 30. Re-read missed task files only — driven by your `progress/weak-spots.md` ledger (local, gitignored — create it from [progress/weak-spots-template.md](progress/weak-spots-template.md)): every OPEN/QUEUED/VERIFY row gets one cold item; a fail sends you to the task file named in the row

## Scenario check (after phase 4, or as you hit them)

- [ ] Customer support agent
- [ ] Code generation with Claude Code
- [ ] Multi-agent research
- [ ] Developer productivity
- [ ] CI/CD
- [ ] Structured extraction
