# Domain 5 — Context Management & Reliability (15%)

Smallest weight. If you get this wrong, Domain 1 coordinators drop IDs, Domain 2 errors look like empty success, and Domain 4 “97% accurate” pipelines ship garbage on one document type.

Same rhythm: one file, check questions, next. Then [practice.md](practice.md) (6 questions, target 5/6).

| Task | File | You must not do |
|---|---|---|
| 5.1 | [5.1-preserve-critical-info.md](5.1-preserve-critical-info.md) | Summarise amounts and order IDs away |
| 5.2 | [5.2-escalation.md](5.2-escalation.md) | Escalate on sentiment or vibe-confidence; pick the first John Smith |
| 5.3 | [5.3-error-propagation.md](5.3-error-propagation.md) | Empty success; kill the whole job; omit coverage gaps |
| 5.4 | [5.4-large-codebases.md](5.4-large-codebases.md) | Keep all grep noise in the parent; no scratchpad |
| 5.5 | [5.5-human-review.md](5.5-human-review.md) | Automate on 97% overall |
| 5.6 | [5.6-provenance.md](5.6-provenance.md) | Drop sources; pick one conflicting number |

## Scenarios

Appears almost everywhere; heaviest in Customer Support, Multi-Agent Research, Structured Extraction.

## Three rules

1. **Gold dust never enters the summary.** Case facts (IDs, amounts, dates) are a persistent block in every prompt.
2. **Escalate on policy, capability, or an explicit human request** — not mood, not uncalibrated confidence.
3. **Keep both claims with sources.** Failures travel as structured errors with partials. Gaps get annotated, not erased.
