# Anti-patterns the exam tests

If an option looks like one of these, it is almost certainly wrong.

## Domain 1

- Parse assistant text for “I’m done” / “completed”
- Stop after N loops as the **primary** completion rule
- `content[0].type == "text"` means finished
- Subagents inherit the coordinator’s history
- Subagents share memory across invocations
- Subagents call each other directly
- Always run the full subagent pipeline
- Prompt-only “always verify the customer” for refunds
- Few-shot examples as the fix for a financial skip rate
- Routing classifier when the bug is **ordering**, not availability
- Resume a session whose tool results are stale
- Re-run the entire baseline analysis to compare two strategies

## Domain 2

- One-line tool descriptions for overlapping tools
- Merge tools as the first fix
- 18 tools on a single agent
- Bash when Read/Grep/Glob/Edit exist
- Write over an existing file
- Hardcoded secrets in `.mcp.json`
- `"Operation failed"` with no category or retry flag
- Treat timeout as an empty successful result

## Domain 3

- Team standards in `~/.claude/CLAUDE.md`
- Team commands in `~/.claude/commands/`
- Always plan mode, or never plan mode
- Interactive Claude Code in CI
- Self-review in the generation session
- “Make it better” with no tests or examples

## Domain 4

- “Output as JSON” in the prompt as a guarantee
- Regex-parse unstructured model text
- Schema match = correct data
- Generic retry: “there was an error”
- Rigid enums with no `other`
- Batches API for latency-sensitive PR review
- Same-session self-review instead of an independent instance
- One-shot review of 14 files

## Domain 5

- Progressive summarisation of order IDs and refund amounts
- Compact **before** gold dust is in case facts / scratchpad
- Escalate on sentiment or uncalibrated self-reported confidence
- Investigate first when the customer already asked for a human
- Heuristic pick among multiple customer matches
- Drop or average conflicting sources
- Silent empty results from a failed subagent
- Kill the whole workflow because one spoke timed out
- Automate on 97% overall accuracy
- Flatten financial figures into prose so numbers cannot be checked
