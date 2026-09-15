# Weak-spots ledger — recheck before the exam

Every check question, gap-check item or practice item that was **failed or half-answered**
since 31 Aug 2026, with where it showed, what it is now, and how to recheck it cold at the
end of the journey (step 30). Kept in the repo on purpose: `HANDOFF.md` is rewritten every
sitting; this file is not.

**Status key.** `OPEN` — still failing or recurring; `QUEUED` — a cold retest is already
booked (mixed set, step 28); `VERIFY` — closed once, needs one more cold pass to count as
closed; `CLOSED` — passed cold at practice level on a different day from the teaching.

**How to recheck (the protocol for step 30).** One cold item per row, in a costume the row
has not seen, letters **and** a why. A pass needs the right letter *and* a why that kills all
three distractors. Two passes on different days close a row; one fail reopens it and sends
you back to the task file named in the row.

---

## Domain 1 — Agentic architecture (27%)

| Weak spot | Where it showed | Status | Recheck as |
|---|---|---|---|
| **Layer attribution** — naming *which* layer/function did something, and *what each layer knows* (request vs client handling; model vs calling code; `run()` vs `search_spoke()`; tool vs hook for the refund limit) | step 6 Q1 (31 Aug); step-14 gap-check G3 (answered about the model when asked about the calling code); exercise 2 gap-check 1b and 5c (14 Sep); Build 1 walkthrough Q5 half — "before the tool" without "the tool doesn't know the caller's authority" (14 Sep); Build 1 gap-check 1a/1c (gate vs model), 5a left BLANK — decided/wrote/delivered across script and Claude Code (15 Sep) | **OPEN — recurring, the top row** | A failure scenario with a trace; ask "which component, and which field proves it" — and "what does that component know that the other cannot" |
| Narrow decomposition vs failure to *dynamically select* spokes (1.2) | step 7 Q2 (1 Sep) | VERIFY (D1 practice 10/10) | Coordinator stem where the brief was complete but a spoke was never dispatched |
| Anchoring on the previous verdict; "stake first, mechanism second" (prompt vs gate) | steps 7–9 (1–2 Sep), three rounds | VERIFY (D1 practice, letters alternated) | Two consecutive items whose right answers differ in mechanism |
| Resume vs fresh session under a migration stem (1.7) | 1.7 Q1 half (3 Sep) | VERIFY (D1 practice Q10 correct) | Poisoned tool results vs stale files — which remedy |
| `fork_session`: isolation half missing (only the cost half given) (1.3) | step 8 Q2 (1 Sep) | VERIFY | Shared baseline + isolated divergence; ask for both halves |
| **Circular answers** — restating the fact as the reason ("all traffic goes through the coordinator") | step 7 Q1; 2.3 Q2 relapse (9 Sep) | **OPEN habit** | Any why-question: reject a why that repeats the stem |
| **Fail-open vs fail-closed** — which way a guard defaults when the guard *itself* breaks (Claude Code hook: exit 2 = deny, any other non-zero = "hook broke, call proceeds" → fails open; agent.py's gate crash → run dies → fails closed) | Build 1 gap-check 5c FAIL (15 Sep): answered "yes, blocked" although the brief stated the exit-code rule; the answer was in the text | **OPEN** | A guard with a bug: does the protected action run? Which direction should a money/destructive guard fail, and what one line makes it so |

## Domain 2 — Tool design & MCP (18%)

| Weak spot | Where it showed | Status | Recheck as |
|---|---|---|---|
| **What exactly crosses the boundary** (payload construction, return contract) | G3 fail (step 14); 2.2 Q2 fail (third instance); then D2 practice 7/7 + 3 retests, ex-45 Q2 pass | CLOSED at practice level — one cold verify | A spoke-timeout payload: list the fields, not the location |
| Who fixes a validation error (user vs **model**) — the who-fixes-it ladder | ex-5 gap-check G2 half (10 Sep) | VERIFY | Log shows the model normalising an id; ask who fixed it and why the ladder puts it there |
| Grep vs Glob when the stem *sounds* path-shaped | 2.x MCQ miss; held in D2 practice (9 Sep) | VERIFY | "Find every file that defines X" — name lives in content, not path |
| Descriptions *enlarge* the haystack; similar-pair vs unrelated-many (2.3) | 2.3 Q2 circular relapse, parts 2–3 half (9 Sep) | VERIFY | Routing stem with 14 tools, two near-duplicates |
| Instance fix vs source fix (copy a teammate's `~/.claude.json` vs repo `.mcp.json`) | 2.4 Q1 half (9 Sep); closed in 3.1 MCQ + Build 2 live; **reopened 15 Sep in schema costume** — fixed an unknown enum type by adding one more enum value instead of `other` + freeform detail | **OPEN — third costume** | An enum/schema stem: unknown category arrives; the bait is "add it to the enum" |
| **Empty-vs-error** — in the *timeout* costume (`[]`+ok is the do-not-retry signal) and in the *code* costume (`{"customer": None}` has no `isError` → `is_error` False) | D2 practice pass; **inverted once** 13 Sep (parallel session), corrected twice same day; **wrong again 14 Sep** in Build 1's code walkthrough (said `is_error` True for a valid-empty lookup, cited a gate line) | **OPEN — three costumes** | Turn-2 retry also times out: findings count + Coverage line, with and without partials; plus a code item: given a tool return value, what does line `is_error: bool(output.get("isError"))` produce |

## Domain 3 — Claude Code (20%)

| Weak spot | Where it showed | Status | Recheck as |
|---|---|---|---|
| **Fork direction** — fork protects the *parent's* window from the skill's working, not the skill from the parent | 3.2 Q2, three rounds (12 Sep); D3 gate R1 first instinct "A" (13 Sep) | **QUEUED step 28** | Wrong option = "fork gives the skill a clean context so the parent cannot bias it" |
| Where-without-why — right path, no reason (travels-on-clone) | step 7 lineage; 3.1 Q1 (11 Sep); passed D3 gate path-right-reason-differs | VERIFY | Two options with the same path, only the reason differs |
| **Undersized why** — names one property when the stem needs the discriminating one | 3.3, 3.5 MCQs, 3.6 Q1 half (12 Sep); ex-4 gap-check 2 of 4 (13 Sep); 4.1 MCQ + 4.3 Q2 (15 Sep) — but 4.4–4.6 all properly sized, 4.6 MCQ with four separate autopsies: trending towards closed | **OPEN habit** | Every bonus MCQ: "which distractor does my why fail to kill?" |
| Batches vs per-PR latency (nobody waiting → 24 h window free → 50%) | 3.6 Q1 why half-sized; D3 gate retest pass | VERIFY | Two CI jobs, one blocked developer |
| **Cost mechanics** — turns and *input* dominate, not output length (incremental review re-verifies, not re-discovers) | exercise 2 gap-check 5b miss, 5c half (14 Sep) | **OPEN** | Two runs, same diff, one with prior findings: explain the cost ratio |
| Structured failure in CI — exit-code capture, not just a message (2.2 shape) | exercise 2 gap-check 4b half (14 Sep) | VERIFY | A `set -e` script that dies silently: name both fixes |

## Domain 4 — Prompt engineering (20%)

| Weak spot | Where it showed | Status | Recheck as |
|---|---|---|---|
| What scoring **bands** buy the metric ("what buys resolution") | legacy eval-block Q4 (1 Sep → 7 Sep); **passed cold at D4 gate R1 (15 Sep)** — resolution mechanism unprompted, against the expected-fail prediction | VERIFY | Eval design stem with a 1–10 vs pass/fail choice |
| Score vs **delta**, wrong criterion / Goodhart | legacy eval Q3 half (7 Sep); passed cold D4 gate R2 (15 Sep) — "rewards presence, not validity" | CLOSED | — |
| Ship with/without the one-shot example; delta vs noise | legacy eval Q5 (7 Sep); passed cold D4 gate R3 (15 Sep) with the arithmetic volunteered | CLOSED | — |
| `content[0].text` with thinking enabled → `AttributeError` (mechanism under scenario) | ex-32 Q1 half (7 Sep); passed cold D4 gate R4 (15 Sep) — fixed-index reliance named | CLOSED | — |
| Single cache breakpoint = one span; `read=0` symptom | ex-36 Q3 half (7 Sep) | QUEUED step 28 (breakpoint placement) | Usage numbers → where the breakpoint is |
| Haiku's silent 4096-token **caching** minimum | ex-36 Q4 FAIL, R1 micro-retest pass (7 Sep); D4 gate R5 (15 Sep) right letter, why restated the option | VERIFY | Which `usage` field separates below-minimum (never written) from TTL-expired (rewritten every request) |
| **Reciting notes instead of executing the scenario** | ex-36 Q4 (7 Sep), named habit | **OPEN habit** | Any scenario item: demand the trace, not the definition |
| **Generalise** = apply the learned rule to a case not in the examples (read as "be vague"; inverted — said reasoning makes the model generalise *less*) | 4.2 Q2 FAIL (15 Sep), vocabulary + mechanism | VERIFY | Few-shot with vs without reasoning lines: what does each buy on a layout not in the examples |
| Required field on a sparse source — the schema contract makes invention the only *legal* output (nullable = absence expressible) | 4.3 Q2 half — headline without the mechanism; chain taught, mechanism then run correctly in the micro-retest (15 Sep) | VERIFY | Blank box + required field + forced tool call: walk what the model can legally emit |

## Domain 5 — Context & reliability (15%)

| Weak spot | Where it showed | Status | Recheck as |
|---|---|---|---|
| **Caching across a gap** — "long gap → don't cache at all" trap; 2× (1 h write) vs 1.25× (plain write); the 5–60 min band | D5 practice Q8 miss (11 Sep); ex-45 Q1(a) FAIL, (b) half (8 Sep) | **QUEUED step 28** (bare "don't cache" option; breakpoint placement) | Burst of 10 requests, 20-min gaps: which cache product, and the arithmetic |
| Self-reported **confidence slider** declared good practice (5.2); human-review slider in extraction costume (5.5) | 5.2 Q2 HARD FAIL, 5.5 Q2 FAIL (10–11 Sep); D5 practice rejected both | VERIFY | Slider distractor next to a sentiment distractor; extraction costume |
| **Partials are product, not diagnostics** (5.3) | 5.3 Q1 half (11 Sep); ex-4 gap-check Q1 half (13 Sep) — twice | **OPEN** | Timeout payload with and without partials: what synthesis can write |
| Compression at the boundary before fan-out (it's the *children's* windows) (5.4) | 5.4 Q2 half (11 Sep) | VERIFY | Coordinator concatenating three 8k spoke essays: what changes upstream |
| **Attribution dies on flatten** — citations, conflict adjudication, dates (5.6) | 5.6 Q2 half — gave rendering (11 Sep) | VERIFY | Summarise spoke output to prose before synthesis: name the casualty |
| Trim **per consumer** — coordinator gets `{id, claim, date}`, synthesis gets full mappings once | ex-4 gap-check Q2 half (13 Sep) | **QUEUED step 28 (b)** | Which payload to which consumer, and why both are right |
| Deterministic provenance join (harness joins url/title/date by id) | ex-4 gap-check Q3 answered by teaching in one session, passed in the other (13 Sep) | QUEUED step 28 (c) | Why not ask the spoke to return the URL |
| De-duplication ownership (harness, `source_id`, before extraction) | ex-4 gap-check Q4 (13 Sep) | QUEUED step 28 (d) | Retry returns the same study: where the filter goes |
| **Arithmetic not volunteered** — answers arrive without the asked-for numbers | ex-36/45 caching series (7–8 Sep), confirmed twice | **OPEN habit** | Every cost question: no number, no mark |

## Cross-cutting habits (watch on every item)

1. **Undersized why** → ask "which distractor does my why fail to kill?"
2. **Circular restatement** → a why must add a mechanism the stem did not contain.
3. **Layer attribution** → name the component and the field that proves it.
4. **Reciting vs executing** → trace the scenario; definitions score nothing.
5. **Arithmetic not volunteered** → compute it, show it.
6. **One committed letter** — "B - A" (9 Sep) and "A then C" (13 Sep) are both ambiguous on paper.
7. **Attempts first** — asking for the answers (7 Sep legacy Q4/Q5; 13 Sep parallel session Q2–4) scores as not passed.
8. **Vocabulary** — say so the moment a term is unclear ("harness", 14 Sep; "generalise", 15 Sep); a missed word looks like a missed concept.

## Step-28 mixed-set queue (already booked)

(a) empty-vs-error in timeout costume · (b) trim-per-consumer · (c) deterministic provenance join · (d) dedup ownership · fork direction · caching: bare "don't cache" option · caching: breakpoint placement.
