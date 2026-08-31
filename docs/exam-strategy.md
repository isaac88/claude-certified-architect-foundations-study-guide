# Exam strategy

The exam is consistent. Internalise these three habits and most Domain 1–5 questions collapse to a decision rule.

## 1. Deterministic over probabilistic when stakes are high

If a single failure costs money, leaks data, or breaks compliance, **prompts are not the answer**. Use hooks, prerequisite gates, `tool_choice`, or JSON Schema.

Prompts and few-shot examples are the right answer for tone, style, formatting preferences, and low-stakes routing.

The exam will offer an “enhanced system prompt” option for refunds, identity checks, and transfer limits. Reject it.

## 2. Proportionate fix

Pick the smallest change that addresses the **root cause**.

| Symptom | First fix | Over-engineered distractor |
|---|---|---|
| Two similar tools, wrong one chosen | Expand tool descriptions | Routing classifier, merge tools, fine-tune |
| 18 tools, poor selection | Split tools across subagents (4–5 each) | Longer descriptions, bigger model |
| Agent skips a required step 8% of the time | Programmatic gate | Few-shot, prompt emphasis |
| Review of 14 files is inconsistent | Per-file pass + integration pass | Larger context window, triple-review consensus |

If the option is “first step”, do not pick a rewrite of the architecture.

## 3. Trace failures to their origin

If every subagent succeeded and the report is still incomplete, the coordinator’s **decomposition** was too narrow. Do not blame synthesis, context windows, or search queries unless the stem gives evidence for those.

If the agent says “Let me look that up” and stops, the loop is checking **text**, not `stop_reason`.

If a human agent gets a useless handoff, the summary is not self-contained — humans do not see the transcript.

## How to read a question

1. Identify the scenario and the **stake** (money / security / style / latency / cost).
2. Identify the **failing component** (loop, coordinator, tool description, CLAUDE.md location, schema, session).
3. Eliminate answers that treat a probabilistic control as a guarantee.
4. Eliminate answers that fix a downstream symptom.
5. Prefer the option that is the designed mechanism (`stop_reason`, `Task` tool, `.claude/commands/`, `-p`, `tool_use` + schema).

## Time boxing

- First pass: answer anything you can in under 90 seconds.
- Flag architecture trade-off questions; return with the decision rules sheet in your head.
- Last 10 minutes: every blank gets a guess. No unanswered items.

## Common distractor families

- Parse natural language (“I’m done”) instead of `stop_reason`
- Iteration caps as the primary stop
- Text-block-means-finished
- Subagents inherit parent history
- Prompt-only enforcement for refunds
- Sentiment or self-reported confidence as escalation
- Progressive summarisation of order IDs and amounts
- Bash `cat` instead of Read
- Write instead of Edit
- User-level `~/.claude/` for team-shared config
- Interactive Claude Code in CI
- Self-review in the same session
- Batches API for latency-sensitive PR review
- “Output as JSON” instead of `tool_use`
- Schema compliance treated as semantic correctness
