# Domain 4 practice exam (8 questions)

Timebox: 16 minutes. Target **7/8**.

---

**1. (4.1)** Review bot floods style nits; developers ignore real security hits. Best first move?

- A) “Be conservative” in the prompt
- B) Disable the noisy category; keep security; rewrite that category with examples before re-enabling
- C) Confidence threshold 90% on all findings
- D) More few-shot of style nits so it flags even more consistently

**2. (4.1)** Severity is “high / medium / low” in prose. Findings are inconsistent. What is missing?

- A) A larger model
- B) Concrete **code examples** per severity level
- C) Batches API
- D) `tool_choice: auto`

**3. (4.2)** Long format instructions; every extraction looks different; ambiguous fields flip-flop. Best consistency lever?

- A) Confidence threshold
- B) 2–4 few-shot examples **with reasoning**
- C) Another page of rules
- D) Merge all fields into one string

**4. (4.3)** Downstream needs valid JSON. Occasional parse errors with “respond only with JSON”. Guarantee?

- A) Stricter wording
- B) `tool_use` + JSON Schema + `tool_choice`
- C) Regex repair
- D) Assume schema-valid means totals are correct

**5. (4.3 / 4.4)** Schema-valid JSON; date sits in `invoice_number`. `tool_use` failed to prevent what?

- A) UTF-8
- B) Semantic / field-placement error
- C) That a tool was called
- D) Token limits

**6. (4.4)** PO number is not on the document. Validator fails because the field is required. Next?

- A) Retry with “try again”
- B) Make the field nullable/optional and return null; do not retry to invent a PO
- C) Raise temperature
- D) Batch the document overnight

**7. (4.5)** Manager wants Batches for every-PR review **and** nightly audit.

- A) Batch both
- B) Sync both
- C) Batch nightly only; keep PR review synchronous
- D) Batch PRs; sync nightly

**8. (4.6)** Same session generated the code and reviews it; misses its own bug. 14-file reviews are also patchy.

- A) Same session + “be more critical”; one pass over 14 files
- B) Independent review instance; per-file pass plus cross-file integration
- C) Three self-reviews, keep issues that appear twice
- D) Larger context window, single pass

---

## Answers

| # | Answer | Note |
|---|---|---|
| 1 | B | Trust is global; kill the noisy category |
| 2 | B | Examples, not adjectives |
| 3 | B | Few-shot + reasoning |
| 4 | B | Shape guarantee |
| 5 | B | Schema ≠ truth |
| 6 | B | Absent data: schema/null, not retry |
| 7 | C | Q11 matching rule |
| 8 | B | Isolation + multi-pass |

**Score:** ___ / 8

- 7–8: Domain 4 exam-ready. Do exercise 3.
- 5–6: Re-read missed files.
- ≤4: Re-work 4.3, 4.4, and 4.5 — those are the sneaky ones.
