# Exercise 3 run log — structured extraction pipeline

Model under test: `claude-haiku-4-5` · run 2026-09-16 14:08 UTC · 38 API calls · 79,342 input + 15,315 output tokens

Every document, figure and reference in `fixtures.py` is invented; the numbers below are measurements of this run, not facts about the world.

## Measured checks

| # | Check | Result | Detail |
|---|---|---|---|
| 1 | Forced tool_use returns a parseable record every time | **PASS** | 20/20 forced extractions produced a tool_use block; prose asked for JSON parsed strictly 0/10 and conformed to the shape 10/10 |
| 2 | A document that disagrees with itself is flagged, not corrected | **PASS** | inv-03 stated_total=2484.0 calculated_total=2424.0 conflict_detected=True note='Stated total 2484.00 does not equal calculated total 2424.00 (line items 2020.00 plus tax 404.00).' |
| 3 | A printed but empty box extracts as null, not a placeholder | **PASS** | scan-05 po_number=None under the nullable schema |
| 4 | The same box under a required non-nullable field forces invention | **PASS** | strict schema returned po_number='null' (type str) for the same blank box |
| 5 | A retry on a genuinely absent field stops instead of inventing | **PASS** | attempts returned [None, None]; none is a real reference, so the pipeline stopped and named the rule and schema as the fix |
| 6 | Unenumerated document kinds land on other + freeform detail | **PASS** | oth-06=other/'delivery note', oth-10=other/'bank statement extract' |
| 7 | Few-shot examples do not lose accuracy against zero-shot | **PASS** | zero-shot 97.3% -> few-shot 98.2% of 110 scored fields |
| 8 | The validation-retry loop resolves errors it can resolve | **PASS** | few-shot first-pass findings on 1 documents; still failing after retry: none |

## Stage 1 — "respond only with JSON" (what prose does not guarantee)

- Strict `json.loads` succeeded: **0/10**
- Succeeded only after a regex repair: **10/10**
- Parsed *and* conformed to the field list and enums: **10/10**

| Document | strict parse | after repair | first 60 characters returned | missing fields | bad enums |
|---|---|---|---|---|---|
| inv-01 | no | yes | ````json\n{\n  "document_type": "invoice",\n  "document_type_det` | — | — |
| inv-02 | no | yes | ````json\n{\n  "document_type": "invoice",\n  "document_type_det` | — | — |
| inv-03 | no | yes | ````json\n{\n  "document_type": "invoice",\n  "document_type_det` | — | — |
| rcp-04 | no | yes | ````json\n{\n  "document_type": "receipt",\n  "document_type_det` | — | — |
| scan-05 | no | yes | ````json\n{\n  "document_type": "invoice",\n  "document_type_det` | — | — |
| oth-06 | no | yes | ````json\n{\n  "document_type": "other",\n  "document_type_detai` | — | — |
| cn-07 | no | yes | ````json\n{\n  "document_type": "credit_note",\n  "document_type` | — | — |
| inv-08 | no | yes | ````json\n{\n  "document_type": "invoice",\n  "document_type_det` | — | — |
| rcp-09 | no | yes | ````json\n{\n  "document_type": "receipt",\n  "document_type_det` | — | — |
| oth-10 | no | yes | ````json\n{\n  "document_type": "other",\n  "document_type_detai` | — | — |

## Stage 2 — `tool_choice: "auto"` on a neutral request

Tool called on **3/3** documents.

| Document | called the tool | stop_reason | prose instead |
|---|---|---|---|
| inv-01 | yes | `tool_use` | — |
| inv-02 | yes | `tool_use` | I'll record this invoice from Blueforge Metals into the accounts-payable ledger.… |
| inv-03 | yes | `tool_use` | I'll record this invoice into the accounts-payable ledger.… |

## Stages 3 and 4 — forced tool, zero-shot vs few-shot

| Measure | zero-shot | few-shot (3 examples) |
|---|---|---|
| Field accuracy, first pass | 96.4% | 97.3% |
| Field accuracy, after retry | **97.3%** | **98.2%** |
| …on layouts an example covers | 97.0% | 100.0% |
| …on layouts no example covers | 97.4% | 97.4% |
| Validation findings, first pass | 1 | 2 |
| Retries spent | 1 | 1 |
| Still failing after retry | none | none |

### Per field

| Field | zero-shot | few-shot |
|---|---|---|
| `document_type` | 10/10 | 10/10 |
| `document_id` | 9/10 | 9/10 |
| `issue_date` | 9/10 | 9/10 |
| `vendor_name` | 10/10 | 10/10 |
| `vendor_tax_id` | 10/10 | 10/10 |
| `po_number` | 10/10 | 10/10 |
| `currency` | 10/10 | 10/10 |
| `line_item_count` | 9/10 | 10/10 **+** |
| `stated_total` | 10/10 | 10/10 |
| `payment_status` | 10/10 | 10/10 |
| `conflict_detected` | 10/10 | 10/10 |

### `detected_pattern` tally (first pass)

| Pattern | zero-shot | few-shot |
|---|---|---|
| `calculated_total_wrong` | 0 | 1 |
| `unflagged_total_mismatch` | 1 | 1 |

### Per document, after retry

| Document | layout | example covers it | zero-shot | few-shot | few-shot misses |
|---|---|---|---|---|---|
| inv-01 | plain invoice, ISO dates, VAT line | no | 11/11 | 11/11 | — |
| inv-02 | ASCII table, UK slash date, PO box says '(none supplied)' | no | 11/11 | 11/11 | — |
| inv-03 | prose invoice, long-form date, TOTAL disagrees with its own lines | no | 11/11 | 11/11 | — |
| rcp-04 | email body receipt, no field labels | yes | 11/11 | 11/11 | — |
| scan-05 | OCR-scanned invoice, letter noise, EMPTY PO box | yes | 11/11 | 11/11 | — |
| oth-06 | delivery note - not an enumerated type, no money at all | yes | 10/11 | 11/11 | — |
| cn-07 | credit note, negative amounts, one positive fee | no | 11/11 | 11/11 | — |
| inv-08 | European decimals (comma + space), sparse: no tax id, no PO | no | 11/11 | 11/11 | — |
| rcp-09 | till receipt, two-digit year, cash and change lines | no | 11/11 | 11/11 | — |
| oth-10 | bank statement extract - other, and no document total at all | no | 9/11 | 9/11 | document_id: got '20-44-19 / 30119827' want None; issue_date: got '2025-04-30' want None |

## Stage 5 — the case a retry cannot fix

- Strict schema (`po_number` required, non-nullable) on the blank box: **'null'**
- Nullable schema, validator rule demanding a PO: attempts returned [(None, False), (None, False)] (value, is a real reference)
- Pipeline stopped without accepting an invented value: **True**

> The value is not on the page. The fix is the validator rule (and a nullable schema), not another retry: retrying a genuinely absent field only buys a more confident invention.

## Stage 6 — Message Batches (optional)

- Batch `msgbatch_01YBBZM7mAVupL5sfUxvCynA` ended in **185.6s**, 10/10 succeeded
- Field accuracy: **96.4%** (same prompt and schema as stage 4)
- Failures to resubmit by `custom_id`: none

Nobody is waiting on this path, which is the only reason it is allowed to be a batch; the synchronous stages above stay for the case where somebody is.
