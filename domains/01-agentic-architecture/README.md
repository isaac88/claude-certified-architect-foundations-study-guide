# Domain 1 — Agentic Architecture & Orchestration (27%)

The heaviest domain. Single-agent loops through to coordinator–subagent systems, hooks, decomposition, and session state.

Work the task files in order. Each file: production example, exam traps, check questions. Finish with [practice.md](practice.md).

| Task | File | You must be able to |
|---|---|---|
| 1.1 | [1.1-agentic-loops.md](1.1-agentic-loops.md) | Drive the loop off `stop_reason` |
| 1.2 | [1.2-multi-agent-orchestration.md](1.2-multi-agent-orchestration.md) | Hub-and-spoke; isolation; blame narrow decomposition |
| 1.3 | [1.3-subagent-invocation.md](1.3-subagent-invocation.md) | `Task` tool, explicit context, parallel spawn, `fork_session` |
| 1.4 | [1.4-workflow-enforcement.md](1.4-workflow-enforcement.md) | Gates for money/security; self-contained handoffs |
| 1.5 | [1.5-sdk-hooks.md](1.5-sdk-hooks.md) | PreToolUse / PostToolUse as 100% guarantees |
| 1.6 | [1.6-task-decomposition.md](1.6-task-decomposition.md) | Prompt chaining vs adaptive decomposition |
| 1.7 | [1.7-session-state.md](1.7-session-state.md) | `--resume`, fork, fresh start with a summary |

## Scenarios that carry this domain

- Customer Support Resolution Agent
- Multi-Agent Research System
- Developer Productivity Tools

## Three rules that decide most of Domain 1

1. **`stop_reason` is the only completion signal.** Text is not.
2. **Subagents are blind** unless you put information in their prompt.
3. **Hooks for must-never-fail; prompts for nice-to-have.**
