# Domain 4 — Prompt Engineering & Structured Output (20%)

This is where distractors sound like good engineering. “Be conservative”, “output as JSON”, “batch everything for 50% savings”, “review your own code in the same session” all sound reasonable. They are wrong for the problem in the stem.

Match the **technique to the failure mode**. Same rhythm: one file, check questions, next. Then [practice.md](practice.md) (8 questions, target 7/8).

| Task | File | Failure it fixes |
|---|---|---|
| 4.1 | [4.1-explicit-criteria.md](4.1-explicit-criteria.md) | Vague instructions → false positives / lost trust |
| 4.2 | [4.2-few-shot.md](4.2-few-shot.md) | Inconsistent format or judgement; missing fields that *are* in the source |
| 4.3 | [4.3-structured-output.md](4.3-structured-output.md) | Malformed JSON; forced fabrication; wrong `tool_choice` |
| 4.4 | [4.4-validation-retry.md](4.4-validation-retry.md) | Semantic errors that retries can (and cannot) fix |
| 4.5 | [4.5-batch-processing.md](4.5-batch-processing.md) | Cost vs latency; blocking vs overnight |
| 4.6 | [4.6-multi-pass-review.md](4.6-multi-pass-review.md) | Self-review bias; attention dilution |

## Scenarios that carry this domain

- Claude Code for CI/CD
- Structured Data Extraction

## Three rules

1. **Criteria and examples beat vibes.** Not “be conservative”. Not confidence as a substitute for a category.
2. **`tool_use` + schema guarantees shape, not truth.** Retry with field errors when the source contains the data; stop when it does not.
3. **Blocking work stays synchronous.** Independent reviewer. Per-file then integration — not one giant pass.
