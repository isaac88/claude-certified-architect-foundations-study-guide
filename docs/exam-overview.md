# Exam overview

## What the credential tests

The exam tests whether you can **choose the right architecture for a production Claude system**, not whether you can recite API field names. Almost every question is a scenario: something is failing in production; four fixes are offered; three look reasonable.

You are expected to have roughly six months of hands-on work with Claude APIs, the Agent SDK, Claude Code, and MCP.

## Format

- 60 multiple-choice questions
- 120 minutes (~2 minutes per question)
- One correct answer, three plausible distractors
- Closed book, no AI assistance
- 4 of 6 production scenarios selected at random for your sitting
- Scaled score 100–1,000; pass at **720**
- Unanswered questions score as incorrect — guess rather than skip
- Score report with domain breakdowns within about two business days

## The six scenarios

Questions are framed inside these production contexts. Details in [scenarios.md](scenarios.md).

1. Customer Support Resolution Agent
2. Code Generation with Claude Code
3. Multi-Agent Research System
4. Developer Productivity with Claude
5. Claude Code for CI/CD
6. Structured Data Extraction

Domain 1 appears most heavily in **1, 3, and 4**.

## In scope vs out of scope

**In scope:** agentic loops, hub-and-spoke, hooks, CLAUDE.md, MCP, tool descriptions, structured errors, plan mode, CI `-p` mode, few-shot, `tool_use` + JSON Schema, Message Batches API, case-facts blocks, escalation, provenance.

**Out of scope:** fine-tuning, model internals, pricing trivia, competing-model comparisons, general software engineering unrelated to Claude, cloud provisioning, RLHF research.

## Core technologies named on the blueprint

Claude Agent SDK · MCP · Claude Code · Messages API · Message Batches API · JSON Schema · Pydantic · CLAUDE.md · built-in tools (Read, Write, Edit, Bash, Grep, Glob)
