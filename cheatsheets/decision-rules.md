# Decision rules (memorise)

Print this. If you can apply every row under time pressure, Domain 1 is largely done and the other domains follow the same logic.

## Loop and orchestration

| Situation | Do this |
|---|---|
| Should the agent keep going? | `stop_reason == "tool_use"` continue; `"end_turn"` stop |
| Text block in the response | Irrelevant to completion. Content can mix `text` and `tool_use` |
| Safety against infinite loops | Cap is a fuse, not the completion condition |
| Unknown next step | Model-driven loop (Claude picks the next tool) |
| Path is fixed and cheap | Workflow / prompt chain, not an agent |
| Multi-agent shape | Hub-and-spoke; spokes never talk to each other |
| Subagent context | Explicit prompt payload only. No inheritance, no shared memory |
| Coordinator cannot spawn subagents | `allowedTools` missing `"Task"` |
| Need speed on independent research | Multiple `Task` calls in **one** coordinator turn |
| Compare two approaches from one analysis | `fork_session` |
| Report covers only a slice of the topic | Coordinator decomposition was too narrow |

## Enforcement

| Stake | Control |
|---|---|
| Money, security, compliance, identity | Hook / programmatic gate |
| Tone, style, formatting preference | Prompt / few-shot |
| Must call a specific tool first | `tool_choice` forced, or a prerequisite gate |
| Heterogeneous tool payloads | `PostToolUse` normalisation |
| Block or redirect a call | `PreToolUse` interception |
| Human takeover | Self-contained handoff: IDs, summary, root cause, amounts, recommended action |

## Tools and MCP

| Situation | Do this |
|---|---|
| Wrong sibling tool chosen | Expand descriptions (inputs, examples, boundaries) — first |
| 18 tools on one agent | Split to specialists, 4–5 tools each |
| Team MCP config | Project `.mcp.json` + `${ENV_VAR}` |
| Personal MCP | `~/.claude.json` |
| Read a file | `Read`, not Bash `cat` |
| Patch existing file | `Edit`, not `Write` |
| Search file contents | `Grep` |
| Find files by name | `Glob` |
| Tool failed | Structured error: category, retryable flag, what was tried, partial results |
| Empty list, query succeeded | Not an error — do not retry |
| Timeout / auth | `isError`; retry only if transient |
| Standard SaaS (Jira, GitHub) | Community MCP server first; custom only if the workflow cannot map |
| Must call a tool this turn | `tool_choice: "any"` or forced `{name}` |
| Simple checks on a specialist | Scoped tool on that agent, not a hub round-trip |

## Claude Code

| Situation | Do this |
|---|---|
| Team instructions | Project `.claude/CLAUDE.md` |
| New hire missing team behaviour | Those instructions are in `~/.claude/` — move to the repo |
| Which memory files loaded? | `/memory` |
| Team slash command | `.claude/commands/` |
| Personal command / skill | `~/.claude/commands/` or `~/.claude/skills/` (different name) |
| Always-on vs on-demand | CLAUDE.md/rules vs commands/skills |
| Conventions by file type across many folders | `.claude/rules/` with glob `paths` |
| Isolate noisy exploration | Skill with `context: fork` + `allowed-tools` |
| Claude interprets a transform differently each run | 2–3 input/output examples first |
| Interacting fixes | One message; independent fixes may be sequential |
| Multi-file architecture | Plan mode; then direct to implement |
| Small well-scoped edit | Direct execution |
| Verbose discovery | Explore subagent; summary back to parent |
| CI hang waiting for input | `-p` / `--print` |
| CI structured output | `--output-format json` and `--json-schema` |
| Review code Claude just wrote | **New session** |
| Re-review after new commits | Prior findings in context; report only new/unfixed |
| Resume named work | `--resume <name>` |
| Resume last session | `--continue` |
| Files changed since last session | Tell the agent which files changed |
| History is stale | Fresh session + structured summary beats resume |

## Prompts and output

| Situation | Do this |
|---|---|
| High false positives | Explicit categorical criteria; **disable** the noisy category while you fix it |
| Severity labels inconsistent | Code examples per level, not adjectives |
| Format / ambiguous cases | 2–4 few-shot examples **with reasoning** |
| Must be valid JSON shape | `tool_use` + schema + `tool_choice` (`any` or forced name; not `auto` if you must extract) |
| Schema-valid but wrong values | Semantic validation; retry with original + failed JSON + field errors |
| Field absent from source | Nullable schema; **do not** retry to invent |
| Unknown document type | Enum + `other` / `unclear` + detail field |
| Overnight bulk, not blocking | Message Batches API (~50% cheaper, up to 24h); `custom_id`; resubmit failures only |
| PR review, user waiting | Synchronous Messages API |
| Retry loop needs many tool turns | Synchronous — Batches has no multi-turn in one request |
| 14-file review is patchy | Per-file pass + integration pass (attention dilution) |
| Review of code just generated | **Independent instance** (no generator context) |

## Context and reliability

| Situation | Do this |
|---|---|
| IDs, dates, amounts across long chat | Immutable case-facts block; never summarise it |
| Lost in the middle | Key findings at the **start**; section headers |
| Verbose tool output | Trim to needed fields **before** append; upstream returns structured facts |
| Customer asks for a human | Escalate **immediately** |
| Frustrated but issue is simple | Acknowledge; offer resolution; escalate if they **reiterate** they want a human |
| Policy silent / cannot progress | Escalate |
| Multiple identity matches | Ask for another identifier; never pick first / most recent |
| Spoke timeout | Structured error + partials; coverage note; do not empty-success or kill the job |
| Conflicting research claims | Keep both with provenance **and dates**; never average |
| Long codebase exploration | Scratchpad **then** `/compact`; subagents; manifest for crash recovery |
| 97% overall accuracy | Stratify by document type **and** field; sample high-confidence too |
