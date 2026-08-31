# Domain 5 practice exam (6 questions)

Timebox: 12 minutes. Target **5/6**.

---

**1. (5.1)** After many turns, order **#8891** and **$247.83** become “a recent refund”. Best preservation?

- A) More aggressive summarisation
- B) Persistent **case-facts** block in every prompt; never summarise those fields
- C) Drop early messages to save tokens
- D) Sentiment-based reset

**2. (5.2)** First message: “I want a human.” Issue looks like a simple tracking lookup. Correct action?

- A) Resolve tracking first to save the human
- B) Escalate immediately
- C) Escalate only if sentiment is negative
- D) Escalate if self-confidence < 70%

**3. (5.2)** Lookup returns five “Ada Lovelace” accounts. Next?

- A) Pick the most recently active
- B) Pick the first row
- C) Ask for another identifier (email, phone, order number)
- D) Average the five customer IDs

**4. (5.3)** Search spoke times out after two abstracts. Coordinator should receive?

- A) `[]` marked success
- B) Process-killing exception
- C) Structured error: type, query tried, partials, alternatives; synthesis **coverage note** if you proceed
- D) “unavailable” with no payload

**5. (5.4 / 5.5)** Overnight repo exploration goes vague; separately, leadership cites 97% extraction accuracy to remove humans. Best pairing?

- A) Keep all Grep in parent context; automate on 97%
- B) Scratchpad + subagents + `/compact` after gold dust is saved; **stratify** accuracy by document type/field before automating
- C) Compact first so IDs shrink; use uncalibrated 0.9 confidence
- D) One Read of repo root; disable review

**6. (5.6)** Two journals give different geothermal MW figures (2019 vs 2024). Synthesis should?

- A) Average them
- B) Keep the higher
- C) Keep **both** with claim–source mappings **and dates**
- D) Drop geothermal

---

## Answers

| # | Answer | Note |
|---|---|---|
| 1 | B | Gold dust never enters the summary |
| 2 | B | Explicit human request → immediate |
| 3 | C | No heuristic pick |
| 4 | C | Structured error + coverage, not silence or kill |
| 5 | B | Exploration hygiene + aggregate-metric trap |
| 6 | C | Provenance + temporal; never average |

**Score:** ___ / 6

- 5–6: Domain 5 exam-ready. Do exercise 4.
- 3–4: Re-read missed files (usually 5.1, 5.2, 5.6).
- ≤2: Re-work 5.1–5.3 before 5.4–5.6.
