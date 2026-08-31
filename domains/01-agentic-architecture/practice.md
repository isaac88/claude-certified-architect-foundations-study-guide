# Domain 1 practice exam (10 questions)

Scenario-style, one correct answer. Timebox: 20 minutes. Answers at the bottom — do not peek.

Mark `/10`. Below 8, revisit the listed task files.

---

**1.** A customer-support agent sometimes replies “Let me look that up.” and stops. Logs show the assistant message contains a `text` block followed by a `tool_use` block. The developer’s loop is:

```python
if response.content[0].type == "text":
    return response.content[0].text
```

What is the correct fix?

- A) Increase `max_tokens` so the model finishes the tool call in the same text block
- B) Terminate only when `stop_reason == "end_turn"`; on `"tool_use"` execute every tool block and append results
- C) If the text contains “look that up”, wait 2 seconds and call the API again
- D) Cap the loop at 5 iterations so a stuck text reply cannot hang the process

**2.** You need an agent that investigates unfamiliar production incidents. The next tool depends on the previous result. Which design matches the exam preference?

- A) A hardcoded sequence: logs → metrics → deploy history → reply
- B) A model-driven loop: Claude chooses tools from accumulating `tool_result`s until `end_turn`
- C) Ten few-shot traces of past incidents in the system prompt, no tools
- D) A classifier that maps incident titles to a fixed runbook ID

**3.** A research coordinator always runs web search, then document analysis, then synthesis, even when the user attached the only document that matters. What should change?

- A) Give every subagent the full coordinator history so they can skip themselves
- B) Let the document agent call the synthesis agent directly when search is unnecessary
- C) Coordinator dynamically selects spokes from the query instead of a fixed pipeline
- D) Raise the iteration cap on the coordinator loop

**4.** A report on “renewable energy technologies” covers only solar and wind. All subagents completed successfully. Most likely root cause?

- A) Synthesis context window dropped later sections
- B) Coordinator decomposed the topic into solar and wind only
- C) Web search API rate-limited other queries
- D) Report template lacked headings for other sources

**5.** Synthesis emits claims with no URLs. Search and document agents logged sources correctly. Best fix?

- A) Increase synthesis `max_tokens`
- B) Pass structured claim–source mappings in the synthesis prompt; forbid unmapped claims
- C) Share the coordinator’s full conversation with synthesis
- D) Ask synthesis in prose to “remember to cite sources”

**6.** Production: 8% of refunds run without account-ownership verification, sometimes crediting the wrong customer. Best change?

- A) Stronger system prompt: always call `get_customer` first
- B) Few-shot examples of the correct order
- C) A prerequisite gate / PreToolUse hook that blocks `process_refund` until a verified customer ID exists
- D) A routing classifier that disables `process_refund` on non-refund wording

**7.** An agent must never execute international transfers until compliance checks pass. One miss is a legal incident. Choose:

- A) Prompt: “always run compliance checks”
- B) PreToolUse hook that denies the transfer tool until checks have succeeded
- C) PostToolUse logging of transfers for a weekly audit
- D) Fine-tune on compliance dialogues

**8.** A 14-file PR review in one pass is patchy: some files deep, some shallow, same pattern flagged in one file and ignored in another. Best restructure?

- A) Larger-context model, same single pass
- B) Per-file local passes, then a cross-file integration pass
- C) Three full-PR reviews; keep issues that appear twice
- D) Ask authors to split every PR to three files

**9.** You have finished a shared codebase analysis and want to compare a characterisation-test strategy with a contract-test strategy without repeating the analysis. Mechanism?

- A) `--continue` twice in the same session
- B) `fork_session` from the analysis baseline
- C) Two new sessions, paste the analysis by hand into both
- D) One session, sequential: do characterisation tests then overwrite with contract tests

**10.** You `--resume` a named investigation after a large migration landed. Prior `Read` results are in history. Safest approach for questions about current code?

- A) Resume and ask immediately — the agent will notice git changes
- B) Resume and tell the agent which files changed, instructing it to re-read them
- C) Always `--continue` instead of `--resume`
- D) Delete tool results from history but keep assistant reasoning

---

## Answers

| # | Answer | Task | If you missed it |
|---|---|---|---|
| 1 | B | 1.1 | Text can sit beside `tool_use`. Only `stop_reason` completes. |
| 2 | B | 1.1 | Unknown path → model-driven loop. A is a workflow. |
| 3 | C | 1.2 | Dynamic selection. Do not always run the full pipeline. |
| 4 | B | 1.2 | Narrow decomposition. Downstream success does not imply coverage. |
| 5 | B | 1.3 | Isolation: metadata must be passed in structure. D is a prompt hope. |
| 6 | C | 1.4 | Financial stake → programmatic gate. A/B are probabilistic. |
| 7 | B | 1.5 | Legal stake → PreToolUse. C is after the fact. |
| 8 | B | 1.6 | Attention dilution. Bigger windows do not fix attention quality. |
| 9 | B | 1.3 / 1.7 | Fork from a shared baseline. |
| 10 | B | 1.7 | Resume does not see disk changes. Tell it, then re-read. If results are badly stale, fresh + summary. |

**Score:** ___ / 10

- 9–10: Domain 1 is exam-ready. Move to Domain 2.
- 7–8: Re-read the missed task files and the [decision rules](../../cheatsheets/decision-rules.md).
- ≤6: Re-work 1.1, 1.2, and 1.4 before anything else.
