# Exercise 3 — structured extraction pipeline (Domain 4 lab)

> ⚠️ **Spoiler — worked solution.** Attempt the brief in [docs/exercises.md](../../docs/exercises.md) first.

Ten invented supplier documents in ten layouts, and the six points of the
brief in [docs/exercises.md #3](../../docs/exercises.md) each measured rather
than asserted: a JSON-Schema extraction tool (4.3), forced `tool_choice`
against "respond only with JSON" (4.3), a validation-retry loop with
field-level errors and one case it *cannot* fix (4.4), `stated_total` /
`calculated_total` / `conflict_detected` plus a `detected_pattern` tally
(4.4), a zero-shot versus few-shot comparison on all ten documents (4.2),
and the optional Message Batches path (4.5).

## Files

| File | What it is |
|---|---|
| [fixtures.py](fixtures.py) | The corpus: ten documents, every organisation, figure and reference invented, plus the gold answers for eleven scored fields. Also the three few-shot examples — separate invented documents, never corpus documents, each with the reasoning behind the call. |
| [extract.py](extract.py) | The pipeline: schema, prompts, deterministic validators, the retry loop, scoring, the six stages, and the log writer. |
| [run-log.md](run-log.md) | Generated, committed: the checks table and every measurement below. |
| [run-results.json](run-results.json) | Generated, committed: every record, finding and score, for re-reading without re-spending. |

## Run it

```bash
# from the repo root; ANTHROPIC_API_KEY from the environment or academy/course-c-claude-api/.env
.venv/bin/python practice/exercise-3-extraction-pipeline/extract.py
.venv/bin/python practice/exercise-3-extraction-pipeline/extract.py --batch   # also stage 6
```

About three minutes, 38 synchronous calls on `claude-haiku-4-5` (override with
`EXTRACT_MODEL`). The course model is deliberate: a larger model scores near
the ceiling on both arms and the few-shot comparison measures nothing.

## What the committed run showed

**Stage 1 — "respond only with JSON" is not the guarantee.** The prose prompt
said *no prose, no code fence, nothing before or after the JSON*. Strict
`json.loads` succeeded on **0 of 10**. Every response was well-formed JSON
inside a ` ```json ` fence, and a regex repair recovered all ten. That is the
honest shape of the failure: the JSON was never the problem, the *wrapper*
was, and no instruction removed it. The repair worked here and is still the
fragile row of the 4.3 table — it guesses at a wrapper the model chooses
afresh each call. Forcing the tool moved the count to **20 of 20** parseable
records across both extraction stages, because the shape stopped being
something the model could decide.

**Stage 2 — `auto` called the tool 3 of 3 times.** Nothing was proved by
that, which is the point worth keeping: on a neutral request ("a document
arrived, take a look") the model chose to extract every time, so the observed
behaviour of `auto` and of a forced call was identical. The difference is not
in what happened but in what *could* happen — `auto` leaves the possibility
of a prose answer in a pipeline whose next step is a parser, and a forced
`tool_choice` removes it.

**Stages 3 and 4 — few-shot fixed exactly what it covered.**

| | zero-shot | few-shot (3 examples) |
|---|---|---|
| Field accuracy after retry | 97.3% | **98.2%** |
| Layouts an example covers | 97.0% | **100.0%** |
| Layouts no example covers | 97.4% | 97.4% |

The three examples closed the covered layouts completely and moved the
uncovered ones **not at all**. The whole gain is one field on the delivery
note (`line_item_count`: the priced-lines habit had suppressed goods lines
that carry no price, and the despatch-note example shows precisely that).
Against 4.2's claim that the reasoning generalises, this run is a caution:
with a corpus this close to the ceiling, what the examples bought was the
layouts they demonstrated. The two surviving misses are on the one document
no example resembles.

**Stage 5 — the case a retry cannot fix, in two costumes.** `scan-05` prints
a PO box and leaves it empty.

- Under the nullable schema, `po_number` came back `None` — correct, and the
  only honest answer available.
- Under a schema where `po_number` is required and **non-nullable**, the same
  blank box produced the four-character *string* `'null'`. Forbidden from
  emitting an absence, the model faked one in-band; a downstream consumer now
  holds a string in a reference field and cannot distinguish it from a real
  PO number.
- Under the nullable schema plus a validator rule that wrongly insists
  invoices carry a PO, the retry — carrying the original document, the failed
  record and a specific field-level error — answered `''`. Not a correction:
  the same absence in a costume the validator already knows.

So the pipeline stops. The value is not on the page; the fix belongs to the
rule and the schema, and another retry only buys a more confident invention.

**Stage 6 — Batches, and what a batch cannot do.** The same few-shot
extraction, one request per document, correlated by `custom_id`: 10 of 10
succeeded, the batch ended in **185.6s**, and field accuracy came out at
**96.4%** against the synchronous path's 98.2%. The gap is not the API being
worse at extraction — it is the **validation-retry loop**, which a batch
request cannot run: each request is one turn, and a retry is a *new* request.
The batch arm scores where the synchronous arm scored before its retry
(97.3%), within a point of run-to-run variance. So the shape of the rule
holds from both ends: batch the bulk pass, keep the retry synchronous or
resubmit the failures as a second batch — and keep the synchronous path for
the case where somebody is waiting, which nobody is here. Failures come back
by `custom_id`, so only those are resubmitted.

## Two harness bugs run 1 found, both worth keeping

1. **The harness's own label leaked into an extracted field.** Run 1 opened
   the user turn with "Document oth-10 from the intake queue", and `oth-10`
   came back as the `document_id` of the one page that prints no reference of
   its own. The filing label is something the *harness* knows; the page does
   not. Once both are in the same turn, nothing in the model can tell them
   apart. The prompt now carries the document and nothing else, and that page
   now returns a reference it actually reads (its account number — still a
   miss against gold, but a miss read off the page).
2. **An empty string counted as a value.** Stage 5's first version asked
   `po_number is not None` and so recorded the retry's `''` as a supplied
   reference. The validator already knew better: `''` is in the placeholder
   set. The check now asks whether a *real* reference came back, which is
   what the pipeline actually needed to know.

## How each brief point is built

1. **Schema (4.3).** Sixteen fields, all `required` — required means *present
   in the record*, not *non-null*. The ones a page may not carry are typed
   `["string", "null"]`, so absence is expressible; `document_type` enumerates
   four kinds plus `other`, with `document_type_detail` for what the document
   calls itself; `currency` and `payment_status` both carry `unclear`.
   Formatting rules (ISO dates, decimal commas, what is not a line item) live
   in the descriptions and the system prompt, because the schema enforces
   types and the prompt says how to coerce.
2. **`tool_choice` (4.3).** Stage 1 prose, stage 2 `auto`, stages 3–5 forced
   by name. Measured above.
3. **Validation-retry (4.4).** Deterministic validators — ISO date, PO
   placeholder, `other` without a detail, detail on an enumerated type, the
   arithmetic, an unflagged mismatch, a phantom conflict, a conflict without
   a note. Each finding carries `field`, `expected`, `actual` and
   `detected_pattern`, and the retry turn is the tool loop itself: the
   original document sits in the first user turn, the failed record is the
   assistant's `tool_use`, and the errors return as a `tool_result` with
   `is_error: true`. Stage 5 is the unfixable case.
4. **Self-correction fields (4.4).** `inv-03` states 2484.00 against lines
   that come to 2424.00. The harness does the arithmetic itself and never
   lets the model quietly reconcile the two: `stated_total` is copied exactly,
   `calculated_total` is checked against the recomputed sum, and
   `conflict_detected` plus a one-sentence note carry the disagreement
   forward. `detected_pattern` counts are tallied per arm so a prompt change
   is argued from counts.
5. **Ten documents, few-shot before and after (4.2).** Eleven scored fields
   per document against gold, split by whether an example covered that
   layout.
6. **Batches (4.5).** Optional, behind `--batch`, with the synchronous path
   intact.
