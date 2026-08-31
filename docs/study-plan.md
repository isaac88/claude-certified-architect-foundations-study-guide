# Study plan

The ordered checklist is [study-steps.md](study-steps.md) — use that, not this page, as the daily path.

This file is only the calendar view (4-week vs 2-week). Tick items in [../progress.md](../progress.md).

Official Anthropic Academy courses and the official practice exam beat any unofficial notes. Use this repo to organise recall, not as a substitute. Course list and domain pairing: [academy-courses.md](academy-courses.md).

## 4-week path (recommended)

Run Academy course **C** in week 1, **F** in week 2, **G** in week 3. A/B only if Claude is new. D or E only if that cloud is your job.

## 4-week path (recommended)

### Week 1 — Domain 1 (27%)

- Read every file in `domains/01-agentic-architecture/`
- Recite the agentic loop from memory, including `stop_reason`
- Draw hub-and-spoke on paper: isolation, no spoke-to-spoke traffic
- Memorise: hooks for money/security/compliance; prompts for preferences
- Complete `domains/01-agentic-architecture/practice.md`
- Hands-on: build a 3-tool agent with a real loop (exercise 1)

### Week 2 — Domains 2 and 5

- Tool descriptions as the primary selection signal
- Structured MCP errors (`isError`, category, retryable)
- 4–5 tools per agent; built-in tool selection (Read vs Bash, Edit vs Write)
- Case facts, escalation criteria, provenance, structured subagent errors
- Hands-on: exercise 4 (research pipeline) or deepen exercise 1 with errors + provenance

### Week 3 — Domains 3 and 4

- CLAUDE.md hierarchy, `.claude/commands/`, `.claude/rules/` globs, skills with `context: fork`
- Plan mode vs direct execution
- CI: `-p`, JSON output, independent review session
- Explicit criteria, few-shot, `tool_use` + schema, validation-retry, batches vs sync, multi-pass review
- Hands-on: exercises 2 and 3

### Week 4 — Scenarios, mixed practice, weak domains

- Re-read [scenarios.md](scenarios.md) and [../cheatsheets/decision-rules.md](../cheatsheets/decision-rules.md)
- Complete [../practice/mixed-set.md](../practice/mixed-set.md)
- Official practice exam on Anthropic Academy
- Revisit any domain below 70% on your own sets

## 2-week crash path

**Days 1–3:** Domain 1 in full + Domain 1 practice + exercise 1  
**Days 4–5:** Domain 2 + Domain 5 + cheatsheets  
**Days 6–8:** Domain 3 + Domain 4 + exercises 2–3  
**Days 9–10:** Scenarios + mixed set + official practice exam  
**Days 11–14:** Drill weak task statements only; re-sit mixed set

## Daily habit (30–45 minutes)

1. One task statement file
2. Cover the traps, say the correct mechanism out loud
3. Two practice questions
4. One line in `progress.md`

## Exam week

- Do not learn new mechanisms
- Re-read decision rules and anti-patterns only
- Sleep
