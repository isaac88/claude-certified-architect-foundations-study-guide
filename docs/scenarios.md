# Production scenarios

The exam picks **4 of these 6** at random. Learn the decision points, not the story.

---

## 1. Customer Support Resolution Agent

**Stack:** Agent SDK + MCP tools `get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`. Target: 80%+ first-contact resolution.

**Domains:** 1, 2, 5

| Decision | Correct | Trap |
|---|---|---|
| Loop termination | `stop_reason`: loop on `tool_use`, exit on `end_turn` | Parse “done” from assistant text |
| Refund limits / identity | Hook or programmatic prerequisite | System prompt “always verify first” |
| Escalation | Customer asks for a human, policy gap, capability limit | Sentiment analysis; self-assessed confidence |
| Long conversations | Immutable **case facts** block (IDs, amounts) | Progressive summarisation of those values |
| Handoff | Self-contained summary: customer ID, conversation summary, root cause, refund amount, recommended action | Assume the human can read the transcript |

---

## 2. Code Generation with Claude Code

**Stack:** Claude Code for generate / refactor / debug / document. Custom commands, CLAUDE.md, plan mode.

**Domains:** 3, 5

| Decision | Correct | Trap |
|---|---|---|
| Team standards | Project `.claude/CLAUDE.md` (version-controlled) | `~/.claude/CLAUDE.md` (personal only) |
| Plan vs execute | Plan mode for multi-file architecture; direct execution for well-scoped edits | Always plan, or never plan |
| Isolation | Skills with `context: fork` and `allowed-tools` | Slash commands that dump exploration into the main session |
| Refinement | TDD: failing test → implement → keep tests green | “Make it better” with no verification criteria |
| Team commands | `.claude/commands/` in the repo | `~/.claude/commands/` |

---

## 3. Multi-Agent Research System

**Stack:** Coordinator plus web search, document analysis, synthesis, report subagents. Cited reports.

**Domains:** 1, 2, 5

| Decision | Correct | Trap |
|---|---|---|
| Architecture | Hub-and-spoke; all traffic through the coordinator | Flat shared memory; subagents talk to each other |
| Context | Explicit, task-relevant payload only | Pass the coordinator’s full history |
| Narrow report | Coordinator decomposition was too narrow | Blame synthesis context window or search bias |
| Conflicts | Keep both claims with provenance | Pick one arbitrarily; average values |
| Subagent failure | Structured error: type, attempted actions, partial results, alternatives | Empty success; generic “failed”; kill the whole workflow |
| Attribution | Structured claim–source mappings in context passing | Unstructured prose blobs |

---

## 4. Developer Productivity with Claude

**Stack:** Codebase exploration, legacy understanding, templates. Built-in tools + MCP.

**Domains:** 1, 2, 3

| Decision | Correct | Trap |
|---|---|---|
| Too many tools (18) | 4–5 tools per agent; rest on specialists | Lengthen descriptions; bigger model |
| Read a config file | `Read` | `Bash('cat config.json')` |
| Project MCP | `.mcp.json` with `${ENV_VAR}`, committed | Hardcoded API keys |
| Modify existing file | `Edit` | `Write` (overwrites the whole file) |
| Compare two approaches | `fork_session` from a shared analysis baseline | Run the baseline twice |
| Long exploration | Scratchpad file + Explore subagent | Keep everything in the main context |

---

## 5. Claude Code for CI/CD

**Stack:** Automated review, test generation, PR feedback. Actionable comments, low false positives.

**Domains:** 3, 4

| Decision | Correct | Trap |
|---|---|---|
| Headless run | `-p` / `--print`, `--output-format json` | Interactive mode; pipe stdin |
| Review generated code | **Separate session** (no generator memory) | Self-review in the same session |
| Nightly audit vs PR review | Batches API for nightly; synchronous for PRs | Batch both; sync both |
| Structured review output | `--json-schema` | Regex-parse free text |
| Inconsistent 14-file review | Per-file pass + cross-file integration pass | Larger context window; majority vote of three reviews |

---

## 6. Structured Data Extraction

**Stack:** Unstructured documents → JSON Schema → downstream systems.

**Domains:** 4, 5

| Decision | Correct | Trap |
|---|---|---|
| Guarantee structure | `tool_use` + JSON Schema + `tool_choice` | “Output as JSON”; regex post-process |
| Schema vs truth | Structure is guaranteed; **semantics are not** | Treat schema-valid as correct |
| Retry | Append field-level errors (expected vs actual) | “There was an error, try again” |
| Unknown types | Enum includes `other` + description field; 2–4 few-shot edge cases | Rigid enum that forces a wrong label |
| Missing source data | Do not retry forever — the document does not contain the field | Blind retry loops |
