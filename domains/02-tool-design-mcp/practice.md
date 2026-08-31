# Domain 2 practice exam (7 questions)

Scenario-style. Timebox: 14 minutes. Answers at the bottom.

Target **6/7**. Below 6, re-read the listed task files.

---

**1. (2.1)** `get_customer` and `lookup_order` both say “Retrieves [entity] information.” The agent sends “check the status of order #12345” to `get_customer`. Most effective **first** step?

- A) 5–8 few-shot examples of order queries
- B) Expand each description: inputs, examples, edge cases, explicit boundaries
- C) Keyword router that pre-selects tools
- D) Merge into `lookup_entity`

**2. (2.1)** After you expand those descriptions, order queries still hit `get_customer`. The system prompt contains “Always look up the customer before helping.” What is going on?

- A) Descriptions cannot override `tool_choice: auto`
- B) Keyword-sensitive prompt instructions are creating a false association
- C) You must merge the tools
- D) The model cannot read order-number formats

**3. (2.2)** `get_customer` returns `[]` with HTTP 200. The agent retries three times, then escalates. The account does not exist. Root problem?

- A) Missing `isRetryable: true` on empty lists
- B) Valid empty result treated as an access failure
- C) Need a routing classifier
- D) Empty arrays are invalid MCP

**4. (2.2)** Refund tool: amount exceeds policy. Correct error shape?

- A) Transient, `isRetryable: true`, agent retries with the same amount
- B) Business, `isRetryable: false`, customer-safe explanation, alternative workflow (escalate / refuse)
- C) Validation, retry after the model invents a smaller amount
- D) `isError: false` and an empty receipt so the agent thinks it succeeded

**5. (2.3)** Synthesis bounces to the coordinator for simple fact checks (85% of cases), adding 2–3 round trips and ~40% latency. Best fix?

- A) Full web-search toolkit on synthesis
- B) Scoped `verify_fact` on synthesis; complex cases still go via the hub
- C) Research spokes must pre-verify every possible claim
- D) Ban fact-checking during synthesis

**6. (2.4)** Whole team must use GitHub from Claude Code after clone. Correct setup?

- A) Each person pastes a token into `~/.claude.json` only
- B) Project `.mcp.json` with `${GITHUB_TOKEN}`, committed; tokens stay in the environment
- C) Token hardcoded in `.mcp.json`
- D) System prompt: use `gh` via Bash

**7. (2.5)** Find all callers of deprecated `charge_legacy()`, then locate test files for those callers. Correct first two moves?

- A) Glob `**/*.py`, then Read every file
- B) Grep `charge_legacy` (contents → callers), then Glob (and/or Grep in test paths) for tests tied to those files
- C) Glob `charge_legacy` because Glob searches names and contents
- D) Bash `find | xargs grep`

---

## Answers

| # | Answer | If you missed it |
|---|---|---|
| 1 | B | Descriptions are the selection mechanism. A/C/D are not first steps. |
| 2 | B | Re-read the system prompt after description changes. |
| 3 | B | Empty success ≠ timeout. Do not retry “no account”. |
| 4 | B | Business errors are not retryable. |
| 5 | B | Q9 pattern: scoped cross-role tool. |
| 6 | B | Project MCP + env expansion. |
| 7 | B | Grep = contents, Glob = paths. Never Bash-as-Grep. |

**Score:** ___ / 7

- 6–7: Domain 2 is exam-ready. Continue Phase 2 (Domain 5) or exercise 5.
- 4–5: Re-read the task files for the misses.
- ≤3: Re-work 2.1 and 2.2 before 2.3–2.5.
