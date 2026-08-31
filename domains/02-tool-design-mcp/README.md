# Domain 2 — Tool Design & MCP Integration (18%)

Tools are how Claude acts. If selection is wrong, errors are mute, or eighteen tools sit on one agent, the exam will not let you blame “the model”.

This folder is a full teaching track. Same rhythm as Domain 1: one file, check questions, next file. Finish with [practice.md](practice.md) (7 questions, target 6/7) and the Domain 2 build in [../../docs/exercises.md](../../docs/exercises.md) exercise 5.

| Task | File | You must be able to |
|---|---|---|
| 2.1 | [2.1-tool-interfaces.md](2.1-tool-interfaces.md) | Descriptions are *the* selection mechanism; expand them before anything else |
| 2.2 | [2.2-structured-errors.md](2.2-structured-errors.md) | Four error categories; empty-success vs access failure |
| 2.3 | [2.3-tool-distribution.md](2.3-tool-distribution.md) | 4–5 tools per agent; `tool_choice`; scoped cross-role tools |
| 2.4 | [2.4-mcp-integration.md](2.4-mcp-integration.md) | Project vs user MCP; `${ENV}`; community before custom |
| 2.5 | [2.5-built-in-tools.md](2.5-built-in-tools.md) | Grep vs Glob; Edit vs Read+Write; no Bash when a dedicated tool exists |

## Scenarios that carry this domain

- Customer Support Resolution Agent
- Multi-Agent Research System
- Developer Productivity Tools

## Three rules that decide most of Domain 2

1. **Low-effort, high-leverage first.** Better descriptions before classifiers. Scoped tool before full access. Community MCP server before a custom build.
2. **`isError` must tell the truth.** A successful “no rows” is not a failure. A timeout is not an empty list.
3. **4–5 tools per role.** Overload is a distribution problem, not a prompting problem.

## Exam first-step habit

When the stem says “most effective **first** step”, reject architecture rewrites. Fix the contract in front of the model (description, error shape, tool count, dedicated built-in).
