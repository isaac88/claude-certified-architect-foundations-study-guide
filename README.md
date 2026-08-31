# Claude Certified Architect — Foundations Study Guide

Unofficial personal preparation notes for Anthropic's **Claude Certified Architect (Foundations)** exam (CCA-F).

This is not affiliated with Anthropic. Exam facts below are taken from the public exam blueprint. Treat vendor docs and Anthropic Academy as the source of truth when they disagree with these notes.

## Exam at a glance

| | |
|---|---|
| Questions | 60 multiple choice (1 correct, 3 distractors) |
| Time | 120 minutes |
| Pass mark | 720 / 1,000 (scaled) |
| Guessing | No penalty — answer every question |
| Scenarios | 4 of 6 production scenarios chosen at random |
| Closed book | No AI assistance during the exam |

**Exam habits that score points:** deterministic over probabilistic when stakes are high; proportionate fixes; trace failures to their origin.

## Domain weights

| Domain | Weight | Folder |
|---|---|---|
| 1. Agentic Architecture & Orchestration | 27% | [domains/01-agentic-architecture](domains/01-agentic-architecture/) |
| 2. Tool Design & MCP | 18% | [domains/02-tool-design-mcp](domains/02-tool-design-mcp/) |
| 3. Claude Code Configuration & Workflows | 20% | [domains/03-claude-code](domains/03-claude-code/) |
| 4. Prompt Engineering & Structured Output | 20% | [domains/04-prompt-engineering](domains/04-prompt-engineering/) |
| 5. Context & Reliability | 15% | [domains/05-context-reliability](domains/05-context-reliability/) |

If Domain 1 is weak, you do not pass. Start there.

## How to use this repo

**Start here: [docs/roadmap.md](docs/roadmap.md)** — the execution order, pairing each Anthropic Academy course section with the domain files it feeds.

[docs/study-steps.md](docs/study-steps.md) holds the numbered 1–30 plan that [progress.md](progress.md) ticks; the roadmap says what to do on which day.


All five domains are full teaching tracks.

Printable decision rules live in [cheatsheets/decision-rules.md](cheatsheets/decision-rules.md). Memorise that page.

## Study plan

See [docs/study-plan.md](docs/study-plan.md) for a 4-week and a 2-week path.

## Official resources

Free Anthropic Academy courses (Skilljar) — listed under “Prepare for this exam”. See [docs/academy-courses.md](docs/academy-courses.md) and tick A–G in [progress.md](progress.md).

Code written along with course C lives in [academy/course-c-claude-api](academy/course-c-claude-api/) — runnable exercises with a study header on each, indexed in that folder's README.

Tooling is pinned in [mise.toml](mise.toml) — Python 3.12 and the Anthropic `ant` CLI. Run `mise install github:anthropics/anthropic-cli` if the CLI is missing (note: mise's registry shortname `ant` is Apache Ant, not this).

- Anthropic Academy — register, official practice exam, partner courses
- Claude Agent SDK docs, Claude Code docs, MCP spec
- Messages API: `stop_reason`, tools, `tool_choice`

## Status

All five domain folders are complete teaching tracks (notes, traps, practice sets, exercises).

British English throughout.
