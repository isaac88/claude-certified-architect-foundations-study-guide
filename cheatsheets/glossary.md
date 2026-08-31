# Glossary

| Term | Meaning | Tasks |
|---|---|---|
| Agentic loop | Send request → inspect `stop_reason` → maybe run tools → append results → repeat | 1.1 |
| `stop_reason` | API field: `"tool_use"` continue, `"end_turn"` finished | 1.1 |
| Model-driven | Claude chooses the next tool from context | 1.1 |
| Workflow / prompt chain | Developer hardcodes the step sequence | 1.1, 1.6 |
| Hub-and-spoke | Coordinator in the centre; all traffic through it | 1.2 |
| Context isolation | Subagents do not see parent history unless copied in | 1.2, 1.3 |
| Task tool | Built-in tool that spawns a subagent (alias: Agent tool) | 1.3 |
| AgentDefinition | Name, description, system prompt, tool restrictions for a subagent | 1.3 |
| `fork_session` | Independent branches from a shared baseline | 1.3, 1.7 |
| Prerequisite gate | Code that blocks tool B until tool A succeeded | 1.4 |
| Handoff summary | Self-contained packet for a human who has no transcript | 1.4 |
| PreToolUse | Hook before a tool runs (block, redirect, approve) | 1.5 |
| PostToolUse | Hook after a tool runs (normalise, inspect, block side-effects) | 1.5 |
| Attention dilution | Quality drop when one prompt covers too many files | 1.6, 4.6 |
| Adaptive decomposition | Plan changes as discoveries arrive | 1.6 |
| `--resume` | Continue a **named** Claude Code session | 1.7 |
| `--continue` | Continue the **most recent** session | 1.7 |
| Case facts | Immutable IDs/amounts kept outside summarised history | 1.7, 5.1 |
| `tool_choice` | `auto` / `any` / forced named tool | 2.3, 4.3 |
| MCP | Model Context Protocol — standard tool/resource servers | 2.4 |
| Plan mode | Explore and design before editing | 3.4 |
| `-p` / `--print` | Non-interactive Claude Code for CI | 3.6 |
| Message Batches API | ~50% cheaper, up to 24 hours, no latency SLA | 4.5 |
| Provenance | Source, confidence, timestamp on a claim | 5.6 |
