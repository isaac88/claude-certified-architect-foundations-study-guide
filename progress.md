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
- [ ] 19. Exercise 1 hardened **or** exercise 4 started

## Phase 3 — Domain 3 then Domain 4

- [ ] 20. Domain 3 files 3.1–3.6
- [ ] 21. Domain 3 practice: ___ / 8 (target 7+)
- [ ] 22. Exercise 2 — Claude Code team workflow
- [ ] 23. Domain 4 files 4.1–4.6
- [ ] 24. Domain 4 practice: ___ / 8 (target 7+)
- [ ] 25. Exercise 3 — extraction pipeline

## Phase 4 — Lock together

- [ ] 26. Exercise 4 finished (research pipeline)
- [ ] 27. Decision rules from memory
- [ ] 28. Mixed set: ___ / 12 (target 10+)
- [ ] 29. Official Academy practice exam
- [ ] 30. Re-read missed task files only

## Scenario check (after phase 4, or as you hit them)

- [ ] Customer support agent
- [ ] Code generation with Claude Code
- [ ] Multi-agent research
- [ ] Developer productivity
- [ ] CI/CD
- [ ] Structured extraction
