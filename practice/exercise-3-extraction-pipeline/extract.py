"""Structured extraction pipeline - practice exercise 3 (Domain 4 lab).

Ten invented supplier documents in ten layouts (fixtures.py), and the six
points of the brief in docs/exercises.md #3, each one measured rather than
asserted:

1. EXTRACTION TOOL WITH JSON SCHEMA (4.3) - required fields, nullable fields
   for values the page may not carry, an enum with `other` plus a freeform
   detail, and `unclear` on the two classifications. Required is not the
   opposite of nullable here: every field is required to be PRESENT, and the
   ones a document may not state are allowed to be null. That is what makes
   absence expressible instead of forcing invention.
2. TOOL_USE + TOOL_CHOICE (4.3) - stage 1 runs the same instructions as
   prose with "respond only with JSON" and counts what comes back; stage 2
   runs `tool_choice: auto` on three documents; stage 3 forces the tool by
   name. The measurement is what each guarantees, not what each happened to
   do once.
3. VALIDATION-RETRY (4.4) - deterministic validators produce FIELD-LEVEL
   errors (field, expected, actual, detected_pattern). The retry turn
   carries all three ingredients: the original document (still in the first
   user turn), the failed extraction (the assistant's tool_use), and the
   specific errors (the tool_result). Stage 5 runs the case retry CANNOT
   fix - a field that is absent from the source - and stops instead of
   inventing.
4. SELF-CORRECTION FIELDS (4.4) - `stated_total`, `calculated_total`,
   `conflict_detected` + `conflict_note`; the harness recomputes the
   arithmetic itself and never lets the model quietly rewrite a total.
   `detected_pattern` on every validation finding, tallied at the end, so
   prompt fixes are argued from counts rather than anecdotes.
5. TEN DOCUMENTS, FEW-SHOT BEFORE/AFTER (4.2) - stage 3 zero-shot, stage 4
   with three worked examples carrying reasoning. Scored field by field
   against gold, and split into layouts an example covered versus layouts no
   example covered (does the handling strategy generalise, or only the three
   shown?).
6. BATCHES (4.5, optional) - `--batch` reruns the same few-shot extraction
   through the Message Batches API with `custom_id` correlation, while the
   synchronous path stays for the developer who is waiting.

Run:  .venv/bin/python practice/exercise-3-extraction-pipeline/extract.py
      [--batch]  also submit the bulk run through Message Batches
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from fixtures import DOCUMENTS, FEW_SHOT_EXAMPLES, SCORED_FIELDS

HERE = Path(__file__).parent
REPO_ROOT = HERE.parents[1]
# Same key the course project and exercises 4 and 5 use; load_dotenv never
# overrides an already-exported variable.
load_dotenv(REPO_ROOT / "academy" / "course-c-claude-api" / ".env")

# The course model throughout. A bigger model would hide the few-shot delta
# this exercise is built to measure; override with EXTRACT_MODEL to see that.
MODEL = os.environ.get("EXTRACT_MODEL", "claude-haiku-4-5")
MAX_TOKENS = 2048
RUN_LOG = HERE / "run-log.md"
RESULTS = HERE / "run-results.json"

client = Anthropic()
usage_total = {"input": 0, "output": 0, "calls": 0}


def log(msg: str) -> None:
    """Progress goes to the terminal as it happens; a silent run is a bug."""
    print(msg, flush=True)


def call(**kwargs) -> Any:
    """One messages.create, with usage accounting."""
    resp = client.messages.create(model=MODEL, max_tokens=MAX_TOKENS, **kwargs)
    usage_total["input"] += resp.usage.input_tokens
    usage_total["output"] += resp.usage.output_tokens
    usage_total["calls"] += 1
    return resp


# --------------------------------------------------------------------------
# 1. The schema
# --------------------------------------------------------------------------

LINE_ITEM = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "amount": {
            "type": ["number", "null"],
            "description": "The line amount as a decimal number, negative for credits. Null when the document lists the line without a price.",
        },
    },
    "required": ["description", "amount"],
}


def extraction_tool(nullable_po: bool = True) -> dict:
    """The extraction tool.

    `nullable_po=False` builds the deliberately wrong variant used in stage
    5: po_number required AND non-nullable. Nothing else changes, so the
    stage-5 comparison isolates one schema decision.
    """
    po_field = (
        {
            "type": ["string", "null"],
            "description": (
                "The purchase order / order reference the document quotes. "
                "Null when the document has no PO field, or has one and it "
                "is blank. Never a placeholder such as 'N/A', '(none "
                "supplied)' or '[ ]', and never a number from elsewhere on "
                "the page."
            ),
        }
        if nullable_po
        else {
            "type": "string",
            "description": "The purchase order / order reference the document quotes.",
        }
    )

    return {
        "name": "record_document",
        "description": (
            "Record one supplier document as a structured row for the "
            "accounts-payable ledger. Every field is taken from the document "
            "in front of you; nothing is inferred from other documents."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "document_type": {
                    "type": "string",
                    "enum": ["invoice", "receipt", "credit_note", "purchase_order", "other"],
                    "description": (
                        "The kind of document. Use 'other' for any kind not "
                        "listed - do not force it into a neighbouring value."
                    ),
                },
                "document_type_detail": {
                    "type": ["string", "null"],
                    "description": (
                        "Required when document_type is 'other': what the "
                        "document calls itself, lower case (for example "
                        "'delivery note', 'bank statement extract'). Null for "
                        "every other type."
                    ),
                },
                "document_id": {
                    "type": ["string", "null"],
                    "description": "The document's own reference number, verbatim. Null if it has none.",
                },
                "issue_date": {
                    "type": ["string", "null"],
                    "description": (
                        "The date the document was issued, normalised to ISO "
                        "8601 (YYYY-MM-DD). A two-digit year 24 means 2024. "
                        "Null when the document states no issue date - a "
                        "period or a due date is not an issue date."
                    ),
                },
                "vendor_name": {
                    "type": ["string", "null"],
                    "description": "The issuing organisation, without page annotations such as '(scanned copy)'.",
                },
                "vendor_tax_id": {
                    "type": ["string", "null"],
                    "description": "VAT or tax registration number, verbatim. Null if absent.",
                },
                "po_number": po_field,
                "currency": {
                    "type": "string",
                    "enum": ["GBP", "EUR", "USD", "other", "unclear"],
                    "description": (
                        "ISO code of the amounts on the page. 'unclear' when "
                        "the document carries no amounts or no currency at all."
                    ),
                },
                "line_items": {
                    "type": "array",
                    "items": LINE_ITEM,
                    "description": (
                        "The document's own itemised lines: goods, "
                        "charges, or the transactions a statement lists. "
                        "Tender lines (CASH, CHANGE), subtotals, tax lines "
                        "and totals are NOT line items."
                    ),
                },
                "subtotal": {"type": ["number", "null"], "description": "The net/subtotal line if the document prints one."},
                "tax_amount": {"type": ["number", "null"], "description": "The tax/VAT amount if the document prints one."},
                "stated_total": {
                    "type": ["number", "null"],
                    "description": (
                        "The total the document itself states as payable or "
                        "paid, copied exactly even if it looks wrong. Decimal "
                        "comma and thousands separators become a plain "
                        "decimal number (1 140,00 -> 1140.00). Null when the "
                        "document states no such total - a closing balance is "
                        "not a total."
                    ),
                },
                "calculated_total": {
                    "type": ["number", "null"],
                    "description": (
                        "Line items plus tax_amount, computed by you from the "
                        "lines you recorded. Null when there are no priced "
                        "lines."
                    ),
                },
                "conflict_detected": {
                    "type": "boolean",
                    "description": (
                        "True when the document disagrees with itself - most "
                        "often stated_total not equal to calculated_total. "
                        "Never resolve the disagreement by changing a number; "
                        "record both and flag it."
                    ),
                },
                "conflict_note": {
                    "type": ["string", "null"],
                    "description": "One sentence naming what disagrees with what. Null when conflict_detected is false.",
                },
                "payment_status": {
                    "type": "string",
                    "enum": ["paid", "unpaid", "partially_paid", "unclear"],
                    "description": (
                        "'unclear' when the document says nothing about "
                        "payment. Saying nothing is not the same as unpaid."
                    ),
                },
            },
            "required": [
                "document_type",
                "document_type_detail",
                "document_id",
                "issue_date",
                "vendor_name",
                "vendor_tax_id",
                "po_number",
                "currency",
                "line_items",
                "subtotal",
                "tax_amount",
                "stated_total",
                "calculated_total",
                "conflict_detected",
                "conflict_note",
                "payment_status",
            ],
        },
    }


BASE_INSTRUCTIONS = """\
You record supplier documents into an accounts-payable ledger.

Rules that the schema cannot enforce for you:
- Copy what the page says. If a value is not on the page, the field is null
  (or 'unclear' for a classification). An invented value is worse than a
  null, because nothing downstream can tell the two apart.
- A printed but empty box is an absent value, not a placeholder string.
- Normalise dates to YYYY-MM-DD and amounts to plain decimal numbers.
- Never make the arithmetic agree by editing a number. If the stated total
  and the lines disagree, record both and set conflict_detected.
"""


def few_shot_block() -> str:
    """The 4.2 examples: three layouts, each with the reason for the call."""
    parts = ["\nWorked examples. The reasoning matters more than the values:\n"]
    for ex in FEW_SHOT_EXAMPLES:
        parts.append(f"--- EXAMPLE: {ex['label']} ---\nDOCUMENT:\n{ex['document']}")
        parts.append(f"RECORD:\n{json.dumps(ex['record'], indent=2)}")
        parts.append(f"WHY:\n{ex['reasoning']}\n")
    return "\n".join(parts)


# --------------------------------------------------------------------------
# 4. Validation - deterministic, field level, with detected_pattern
# --------------------------------------------------------------------------

PLACEHOLDERS = {
    "", "-", "--", "n/a", "na", "n.a.", "none", "none supplied",
    "(none supplied)", "not supplied", "not provided", "unknown", "tbc",
    "[ ]", "[]", "blank", "empty", "null",
}
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def validate(rec: dict) -> list[dict]:
    """Return field-level findings. Each carries the pattern that produced it."""
    findings: list[dict] = []

    def add(field, expected, actual, pattern):
        findings.append({"field": field, "expected": expected, "actual": actual, "detected_pattern": pattern})

    if rec.get("issue_date") is not None and not ISO_DATE.match(str(rec["issue_date"])):
        add("issue_date", "ISO 8601 YYYY-MM-DD", rec["issue_date"], "non_iso_date")

    po = rec.get("po_number")
    if isinstance(po, str) and po.strip().lower() in PLACEHOLDERS:
        add("po_number", "null when the document carries no PO", po, "placeholder_instead_of_null")

    if rec.get("document_type") == "other" and not rec.get("document_type_detail"):
        add("document_type_detail", "a freeform name when document_type is 'other'", rec.get("document_type_detail"), "missing_other_detail")

    if rec.get("document_type") != "other" and rec.get("document_type_detail"):
        add("document_type_detail", "null unless document_type is 'other'", rec["document_type_detail"], "detail_on_enumerated_type")

    # The arithmetic is the harness's job, not the model's claim about it.
    amounts = [li.get("amount") for li in rec.get("line_items") or [] if li.get("amount") is not None]
    if amounts:
        computed = round(sum(amounts) + (rec.get("tax_amount") or 0), 2)
        if rec.get("calculated_total") is None or abs(rec["calculated_total"] - computed) > 0.011:
            add("calculated_total", f"{computed} (line items + tax_amount)", rec.get("calculated_total"), "calculated_total_wrong")
        stated = rec.get("stated_total")
        if stated is not None:
            disagrees = abs(stated - computed) > 0.011
            if disagrees and not rec.get("conflict_detected"):
                add("conflict_detected", f"true - stated {stated} vs computed {computed}", rec.get("conflict_detected"), "unflagged_total_mismatch")
            if not disagrees and rec.get("conflict_detected"):
                add("conflict_detected", f"false - stated {stated} equals computed {computed}", True, "phantom_conflict")

    if rec.get("conflict_detected") and not rec.get("conflict_note"):
        add("conflict_note", "one sentence naming the disagreement", None, "conflict_without_note")

    return findings


def error_message(findings: list[dict]) -> str:
    """The retry's third ingredient: specific, per field, expected vs actual."""
    lines = ["The record was rejected by validation. Errors, field by field:"]
    for f in findings:
        lines.append(f"- {f['field']}: expected {f['expected']}; got {json.dumps(f['actual'])} [{f['detected_pattern']}]")
    lines.append(
        "Call record_document again with the whole record corrected. Take every "
        "value from the document above. If a value the errors mention is simply "
        "not on the page, leave it null and do not substitute anything."
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Extraction with the validation-retry loop
# --------------------------------------------------------------------------

def user_prompt(doc: dict) -> str:
    """The document and nothing else.

    Run 1 addressed the model as "Document oth-10 from the intake queue" and
    got document_id="oth-10" back on the one page that prints no reference of
    its own. The harness's filing label is not page content, and a model
    cannot tell the difference once both are in the same turn.
    """
    return f"A document from the intake queue:\n\n<document>\n{doc['text']}</document>"


def extract(doc: dict, *, few_shot: bool, tool: dict | None = None, max_retries: int = 2) -> dict:
    """Force the tool, validate, retry with field-level errors, return the trace."""
    tool = tool or extraction_tool()
    system = BASE_INSTRUCTIONS + (few_shot_block() if few_shot else "")
    messages = [{"role": "user", "content": user_prompt(doc)}]
    trace: dict[str, Any] = {"id": doc["id"], "attempts": [], "record": None, "stopped_unfixable": False}

    for attempt in range(max_retries + 1):
        resp = call(
            system=system,
            messages=messages,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
        )
        block = next((b for b in resp.content if b.type == "tool_use"), None)
        if block is None:
            trace["attempts"].append({"attempt": attempt, "error": "no tool_use block", "findings": []})
            break

        record = block.input
        findings = validate(record)
        trace["attempts"].append({"attempt": attempt, "record": record, "findings": findings})
        trace["record"] = record
        if not findings:
            break
        if attempt == max_retries:
            break

        messages.append({"role": "assistant", "content": resp.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": block.id,
                "is_error": True,
                "content": error_message(findings),
            }],
        })
    return trace


# --------------------------------------------------------------------------
# Scoring against gold
# --------------------------------------------------------------------------

def norm_str(v: Any) -> Any:
    if v is None:
        return None
    s = re.sub(r"\s+", " ", str(v)).strip().lower()
    s = s.strip(" .,:;")
    return s


def field_ok(field: str, got: Any, want: Any) -> bool:
    if field == "line_item_count":
        return len(got or []) == want
    if field in ("stated_total",):
        if want is None or got is None:
            return got is None and want is None
        return abs(float(got) - float(want)) <= 0.011
    if field == "conflict_detected":
        return bool(got) == bool(want)
    return norm_str(got) == norm_str(want)


def score(records: dict[str, dict]) -> dict:
    """Field-by-field accuracy against gold, per document and overall."""
    per_doc = {}
    right = total = 0
    for doc in DOCUMENTS:
        rec = records.get(doc["id"]) or {}
        fields = {}
        for field in SCORED_FIELDS:
            want = doc["gold"][field]
            got = rec.get("line_items") if field == "line_item_count" else rec.get(field)
            ok = field_ok(field, got, want)
            fields[field] = {"ok": ok, "got": (len(got or []) if field == "line_item_count" else got), "want": want}
            right += ok
            total += 1
        per_doc[doc["id"]] = {
            "covered_by_example": doc["covered_by_example"],
            "correct": sum(1 for f in fields.values() if f["ok"]),
            "of": len(SCORED_FIELDS),
            "fields": fields,
        }
    covered = [d for d in DOCUMENTS if d["covered_by_example"]]
    uncovered = [d for d in DOCUMENTS if not d["covered_by_example"]]

    def subset(docs):
        r = sum(per_doc[d["id"]]["correct"] for d in docs)
        t = sum(per_doc[d["id"]]["of"] for d in docs)
        return {"correct": r, "of": t, "pct": round(100 * r / t, 1) if t else 0.0}

    return {
        "per_doc": per_doc,
        "overall": {"correct": right, "of": total, "pct": round(100 * right / total, 1)},
        "layouts_an_example_covers": subset(covered),
        "layouts_no_example_covers": subset(uncovered),
    }


# --------------------------------------------------------------------------
# Stage 1 - "respond only with JSON" (4.3: what prose does not guarantee)
# --------------------------------------------------------------------------

def shape_description() -> str:
    """The same field list as the schema, written out for a prose prompt."""
    props = extraction_tool()["input_schema"]["properties"]
    lines = []
    for name, spec in props.items():
        t = spec.get("type")
        t = "/".join(t) if isinstance(t, list) else t
        enum = f" one of {spec['enum']}" if "enum" in spec else ""
        lines.append(f'  "{name}": {t}{enum}')
    return "{\n" + ",\n".join(lines) + "\n}"


def stage1_prose() -> dict:
    """Ask for JSON in words. Count syntax failures AND conformance failures."""
    system = (
        BASE_INSTRUCTIONS
        + "\nRespond ONLY with a single JSON object in exactly this shape. No "
        "prose, no code fence, no explanation, nothing before or after the "
        "JSON:\n" + shape_description()
    )
    required = extraction_tool()["input_schema"]["required"]
    enums = {k: v["enum"] for k, v in extraction_tool()["input_schema"]["properties"].items() if "enum" in v}

    results = []
    for doc in DOCUMENTS:
        log(f"  [1] prose JSON  {doc['id']}")
        resp = call(system=system, messages=[{"role": "user", "content": user_prompt(doc)}])
        text = "".join(b.text for b in resp.content if b.type == "text")
        row = {"id": doc["id"], "parsed_strict": False, "parsed_after_repair": False,
               "missing_fields": [], "bad_enums": [],
               "raw_prefix": text[:60].replace("\n", "\\n")}
        rec = None
        try:
            rec = json.loads(text)
            row["parsed_strict"] = True
        except json.JSONDecodeError:
            # The "repair after the fact" row of the 4.3 table, measured.
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    rec = json.loads(m.group(0))
                    row["parsed_after_repair"] = True
                except json.JSONDecodeError:
                    pass
        if isinstance(rec, dict):
            row["missing_fields"] = [f for f in required if f not in rec]
            row["bad_enums"] = [f"{k}={rec.get(k)!r}" for k, allowed in enums.items() if k in rec and rec[k] not in allowed]
        row["record"] = rec if isinstance(rec, dict) else None
        results.append(row)

    parsed = sum(r["parsed_strict"] for r in results)
    repaired = sum(r["parsed_after_repair"] for r in results)
    conforming = sum(1 for r in results if r["record"] and not r["missing_fields"] and not r["bad_enums"])
    log(f"  [1] strict parse {parsed}/{len(results)}, after repair {parsed + repaired}/{len(results)}, schema-conforming {conforming}/{len(results)}")
    return {"rows": results, "parsed_strict": parsed, "parsed_after_repair": repaired, "conforming": conforming}


# --------------------------------------------------------------------------
# Stage 2 - tool_choice: auto, on a neutral request (4.3)
# --------------------------------------------------------------------------

def stage2_auto(n: int = 3) -> dict:
    """The tool is available; nothing forces it. Count turns with no tool_use."""
    rows = []
    for doc in DOCUMENTS[:n]:
        log(f"  [2] tool_choice auto  {doc['id']}")
        resp = call(
            system=BASE_INSTRUCTIONS,
            messages=[{"role": "user", "content":
                       f"A document arrived in the intake queue. Take a look at it.\n\n<document>\n{doc['text']}</document>"}],
            tools=[extraction_tool()],
            tool_choice={"type": "auto"},
        )
        used = any(b.type == "tool_use" for b in resp.content)
        text = "".join(b.text for b in resp.content if b.type == "text")
        rows.append({"id": doc["id"], "called_tool": used, "stop_reason": resp.stop_reason, "prose": text[:400]})
    return {"rows": rows, "called_tool": sum(r["called_tool"] for r in rows), "of": len(rows)}


# --------------------------------------------------------------------------
# Stages 3 and 4 - forced tool, zero-shot then few-shot (4.2, 4.3, 4.4)
# --------------------------------------------------------------------------

def run_corpus(few_shot: bool, tag: str) -> dict:
    traces, first_pass, final = {}, {}, {}
    for doc in DOCUMENTS:
        t = extract(doc, few_shot=few_shot)
        traces[doc["id"]] = t
        first_pass[doc["id"]] = t["attempts"][0].get("record") or {}
        final[doc["id"]] = t["record"] or {}
        n_find = len(t["attempts"][0]["findings"])
        log(f"  [{tag}] {doc['id']}  attempts={len(t['attempts'])}  first-pass findings={n_find}")
    patterns: dict[str, int] = {}
    for t in traces.values():
        for f in t["attempts"][0]["findings"]:
            patterns[f["detected_pattern"]] = patterns.get(f["detected_pattern"], 0) + 1
    unresolved = {k: len(t["attempts"][-1]["findings"]) for k, t in traces.items() if t["attempts"][-1]["findings"]}
    return {
        "traces": traces,
        "score_first_pass": score(first_pass),
        "score_final": score(final),
        "detected_patterns": patterns,
        "retries_used": sum(len(t["attempts"]) - 1 for t in traces.values()),
        "unresolved_after_retry": unresolved,
    }


# --------------------------------------------------------------------------
# Stage 5 - the case retry cannot fix (4.4)
# --------------------------------------------------------------------------

SCAN = next(d for d in DOCUMENTS if d["id"] == "scan-05")


def stage5_unfixable() -> dict:
    """scan-05 has a PO box and it is blank. Two ways to ask for it.

    5a asks with po_number required and NON-nullable: the schema makes null
    illegal, so whatever comes back is invention, in one form or another.
    5b asks with the nullable schema, then applies a validator rule that
    wrongly insists invoices carry a PO. The model answers null, the rule
    rejects it, the retry carries the specific error - and the second null
    is the pipeline's signal to STOP and fix the rule, not to ask again.
    """
    log("  [5a] strict schema (po_number required, non-nullable) on scan-05")
    resp = call(
        system=BASE_INSTRUCTIONS,
        messages=[{"role": "user", "content": user_prompt(SCAN)}],
        tools=[extraction_tool(nullable_po=False)],
        tool_choice={"type": "tool", "name": "record_document"},
    )
    strict_block = next(b for b in resp.content if b.type == "tool_use")
    strict_po = strict_block.input.get("po_number")
    log(f"  [5a] po_number came back as {strict_po!r}")

    log("  [5b] nullable schema + a validator rule that demands a PO")
    tool = extraction_tool()
    messages = [{"role": "user", "content": user_prompt(SCAN)}]
    attempts = []
    for attempt in range(2):
        resp = call(system=BASE_INSTRUCTIONS, messages=messages, tools=[tool],
                    tool_choice={"type": "tool", "name": "record_document"})
        block = next(b for b in resp.content if b.type == "tool_use")
        po = block.input.get("po_number")
        real = po is not None and str(po).strip().lower() not in PLACEHOLDERS
        attempts.append({"attempt": attempt, "po_number": po, "is_a_real_reference": real})
        log(f"  [5b] attempt {attempt}: po_number={po!r} (real reference: {real})")
        if real:
            break
        if attempt == 1:
            break
        findings = [{
            "field": "po_number",
            "expected": "a purchase order reference (validator rule: invoices must carry one)",
            "actual": None,
            "detected_pattern": "required_field_absent_from_source",
        }]
        messages.append({"role": "assistant", "content": resp.content})
        messages.append({"role": "user", "content": [{
            "type": "tool_result", "tool_use_id": block.id, "is_error": True,
            "content": error_message(findings),
        }]})

    # The pipeline stops when the retry produced no REAL reference. Run 1
    # is the reason this is not "is not None": under retry pressure the model
    # went from an honest null to an empty string - absence in a costume.
    stopped = not attempts[-1]["is_a_real_reference"]
    return {
        "strict_schema_po": strict_po,
        "strict_schema_invented": strict_po is not None,
        "attempts": attempts,
        "stopped_without_accepting_invention": stopped,
        "conclusion": (
            "The value is not on the page. The fix is the validator rule (and "
            "a nullable schema), not another retry: retrying a genuinely "
            "absent field only buys a more confident invention."
        ),
    }


# --------------------------------------------------------------------------
# Stage 6 - Message Batches, optional (4.5)
# --------------------------------------------------------------------------

def stage6_batch(poll_seconds: int = 600) -> dict:
    """The same few-shot extraction, submitted as a batch, correlated by custom_id.

    Nobody is waiting on this path, which is the whole reason it is allowed
    to be a batch. The synchronous path above stays for the case where
    somebody is.
    """
    system = BASE_INSTRUCTIONS + few_shot_block()
    tool = extraction_tool()
    requests = [{
        "custom_id": doc["id"],
        "params": {
            "model": MODEL,
            "max_tokens": MAX_TOKENS,
            "system": system,
            "messages": [{"role": "user", "content": user_prompt(doc)}],
            "tools": [tool],
            "tool_choice": {"type": "tool", "name": tool["name"]},
        },
    } for doc in DOCUMENTS]

    log(f"  [6] submitting {len(requests)} requests as one batch")
    batch = client.messages.batches.create(requests=requests)
    started = time.time()
    while True:
        b = client.messages.batches.retrieve(batch.id)
        log(f"  [6] {b.processing_status}  counts={b.request_counts}  {int(time.time() - started)}s")
        if b.processing_status == "ended":
            break
        if time.time() - started > poll_seconds:
            return {"batch_id": batch.id, "timed_out_polling": True, "note": "still processing; results retrievable later by batch id"}
        time.sleep(15)

    records, failures = {}, []
    for result in client.messages.batches.results(batch.id):
        if result.result.type != "succeeded":
            failures.append({"custom_id": result.custom_id, "type": result.result.type})
            continue
        msg = result.result.message
        block = next((x for x in msg.content if x.type == "tool_use"), None)
        records[result.custom_id] = block.input if block else {}
    return {
        "batch_id": batch.id,
        "seconds": round(time.time() - started, 1),
        "succeeded": len(records),
        "failed": failures,
        "score": score(records),
        "resubmit_only": [f["custom_id"] for f in failures],
    }


# --------------------------------------------------------------------------
# Measured checks and the log
# --------------------------------------------------------------------------

def build_checks(s1, s2, zero, few, s5) -> list[dict]:
    forced_blocks = sum(1 for r in (zero, few) for t in r["traces"].values() if t["record"])
    conflict = few["traces"]["inv-03"]["record"] or {}
    scan = few["traces"]["scan-05"]["record"] or {}
    oth6 = few["traces"]["oth-06"]["record"] or {}
    oth10 = few["traces"]["oth-10"]["record"] or {}
    return [
        {
            "check": "1. Forced tool_use returns a parseable record every time",
            "pass": forced_blocks == 2 * len(DOCUMENTS),
            "detail": f"{forced_blocks}/{2 * len(DOCUMENTS)} forced extractions produced a tool_use block; "
                      f"prose asked for JSON parsed strictly {s1['parsed_strict']}/{len(DOCUMENTS)} "
                      f"and conformed to the shape {s1['conforming']}/{len(DOCUMENTS)}",
        },
        {
            "check": "2. A document that disagrees with itself is flagged, not corrected",
            "pass": bool(conflict.get("conflict_detected")) and abs((conflict.get("stated_total") or 0) - 2484.00) <= 0.011,
            "detail": f"inv-03 stated_total={conflict.get('stated_total')} calculated_total={conflict.get('calculated_total')} "
                      f"conflict_detected={conflict.get('conflict_detected')} note={(conflict.get('conflict_note') or '')[:120]!r}",
        },
        {
            "check": "3. A printed but empty box extracts as null, not a placeholder",
            "pass": scan.get("po_number") is None,
            "detail": f"scan-05 po_number={scan.get('po_number')!r} under the nullable schema",
        },
        {
            "check": "4. The same box under a required non-nullable field forces invention",
            "pass": s5["strict_schema_invented"],
            "detail": f"strict schema returned po_number={s5['strict_schema_po']!r} "
                      f"(type {type(s5['strict_schema_po']).__name__}) for the same blank box",
        },
        {
            "check": "5. A retry on a genuinely absent field stops instead of inventing",
            "pass": s5["stopped_without_accepting_invention"],
            "detail": f"attempts returned {[a['po_number'] for a in s5['attempts']]}; none is a real reference, so the "
                      f"pipeline stopped and named the rule and schema as the fix",
        },
        {
            "check": "6. Unenumerated document kinds land on other + freeform detail",
            "pass": oth6.get("document_type") == "other" and bool(oth6.get("document_type_detail"))
                    and oth10.get("document_type") == "other" and bool(oth10.get("document_type_detail")),
            "detail": f"oth-06={oth6.get('document_type')}/{oth6.get('document_type_detail')!r}, "
                      f"oth-10={oth10.get('document_type')}/{oth10.get('document_type_detail')!r}",
        },
        {
            "check": "7. Few-shot examples do not lose accuracy against zero-shot",
            "pass": few["score_final"]["overall"]["pct"] >= zero["score_final"]["overall"]["pct"],
            "detail": f"zero-shot {zero['score_final']['overall']['pct']}% -> few-shot {few['score_final']['overall']['pct']}% "
                      f"of {zero['score_final']['overall']['of']} scored fields",
        },
        {
            "check": "8. The validation-retry loop resolves errors it can resolve",
            "pass": (sum(len(t['attempts'][0]['findings']) for t in few['traces'].values()) == 0)
                    or (len(few["unresolved_after_retry"]) < sum(1 for t in few["traces"].values() if t["attempts"][0]["findings"])),
            "detail": f"few-shot first-pass findings on {sum(1 for t in few['traces'].values() if t['attempts'][0]['findings'])} documents; "
                      f"still failing after retry: {few['unresolved_after_retry'] or 'none'}",
        },
    ]


def field_delta_table(zero, few) -> list[str]:
    rows = ["| Field | zero-shot | few-shot |", "|---|---|---|"]
    for field in SCORED_FIELDS:
        z = sum(1 for d in DOCUMENTS if zero["score_final"]["per_doc"][d["id"]]["fields"][field]["ok"])
        f = sum(1 for d in DOCUMENTS if few["score_final"]["per_doc"][d["id"]]["fields"][field]["ok"])
        mark = "" if z == f else (" **+**" if f > z else " **-**")
        rows.append(f"| `{field}` | {z}/{len(DOCUMENTS)} | {f}/{len(DOCUMENTS)}{mark} |")
    return rows


def write_log(s1, s2, zero, few, s5, checks, batch) -> None:
    out: list[str] = []
    w = out.append
    w("# Exercise 3 run log — structured extraction pipeline\n")
    w(f"Model under test: `{MODEL}` · run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
      f"{usage_total['calls']} API calls · {usage_total['input']:,} input + {usage_total['output']:,} output tokens\n")
    w("Every document, figure and reference in `fixtures.py` is invented; the numbers below are "
      "measurements of this run, not facts about the world.\n")

    w("## Measured checks\n")
    w("| # | Check | Result | Detail |")
    w("|---|---|---|---|")
    for c in checks:
        w(f"| {c['check'].split('.')[0]} | {c['check'].split('. ', 1)[1]} | {'**PASS**' if c['pass'] else '**FAIL**'} | {c['detail']} |")
    w("")

    w("## Stage 1 — \"respond only with JSON\" (what prose does not guarantee)\n")
    w(f"- Strict `json.loads` succeeded: **{s1['parsed_strict']}/{len(DOCUMENTS)}**")
    w(f"- Succeeded only after a regex repair: **{s1['parsed_after_repair']}/{len(DOCUMENTS)}**")
    w(f"- Parsed *and* conformed to the field list and enums: **{s1['conforming']}/{len(DOCUMENTS)}**\n")
    w("| Document | strict parse | after repair | first 60 characters returned | missing fields | bad enums |")
    w("|---|---|---|---|---|---|")
    for r in s1["rows"]:
        w(f"| {r['id']} | {'yes' if r['parsed_strict'] else 'no'} | {'yes' if r['parsed_after_repair'] else '—'} | "
          f"`{r.get('raw_prefix', '')}` | {', '.join(r['missing_fields']) or '—'} | {', '.join(r['bad_enums']) or '—'} |")
    w("")

    w("## Stage 2 — `tool_choice: \"auto\"` on a neutral request\n")
    w(f"Tool called on **{s2['called_tool']}/{s2['of']}** documents.\n")
    w("| Document | called the tool | stop_reason | prose instead |")
    w("|---|---|---|---|")
    for r in s2["rows"]:
        w(f"| {r['id']} | {'yes' if r['called_tool'] else '**no**'} | `{r['stop_reason']}` | {(r['prose'][:90] + '…') if r['prose'] else '—'} |")
    w("")

    w("## Stages 3 and 4 — forced tool, zero-shot vs few-shot\n")
    w("| Measure | zero-shot | few-shot (3 examples) |")
    w("|---|---|---|")
    w(f"| Field accuracy, first pass | {zero['score_first_pass']['overall']['pct']}% | {few['score_first_pass']['overall']['pct']}% |")
    w(f"| Field accuracy, after retry | **{zero['score_final']['overall']['pct']}%** | **{few['score_final']['overall']['pct']}%** |")
    w(f"| …on layouts an example covers | {zero['score_final']['layouts_an_example_covers']['pct']}% | {few['score_final']['layouts_an_example_covers']['pct']}% |")
    w(f"| …on layouts no example covers | {zero['score_final']['layouts_no_example_covers']['pct']}% | {few['score_final']['layouts_no_example_covers']['pct']}% |")
    w(f"| Validation findings, first pass | {sum(zero['detected_patterns'].values())} | {sum(few['detected_patterns'].values())} |")
    w(f"| Retries spent | {zero['retries_used']} | {few['retries_used']} |")
    w(f"| Still failing after retry | {zero['unresolved_after_retry'] or 'none'} | {few['unresolved_after_retry'] or 'none'} |")
    w("")
    w("### Per field\n")
    out.extend(field_delta_table(zero, few))
    w("")
    w("### `detected_pattern` tally (first pass)\n")
    w("| Pattern | zero-shot | few-shot |")
    w("|---|---|---|")
    for p in sorted(set(zero["detected_patterns"]) | set(few["detected_patterns"])):
        w(f"| `{p}` | {zero['detected_patterns'].get(p, 0)} | {few['detected_patterns'].get(p, 0)} |")
    if not (zero["detected_patterns"] or few["detected_patterns"]):
        w("| — | 0 | 0 |")
    w("")
    w("### Per document, after retry\n")
    w("| Document | layout | example covers it | zero-shot | few-shot | few-shot misses |")
    w("|---|---|---|---|---|---|")
    for d in DOCUMENTS:
        z = zero["score_final"]["per_doc"][d["id"]]
        f = few["score_final"]["per_doc"][d["id"]]
        misses = [k for k, v in f["fields"].items() if not v["ok"]]
        detail = "; ".join(f"{k}: got {f['fields'][k]['got']!r} want {f['fields'][k]['want']!r}" for k in misses) or "—"
        w(f"| {d['id']} | {d['layout']} | {'yes' if d['covered_by_example'] else 'no'} | {z['correct']}/{z['of']} | {f['correct']}/{f['of']} | {detail} |")
    w("")

    w("## Stage 5 — the case a retry cannot fix\n")
    w(f"- Strict schema (`po_number` required, non-nullable) on the blank box: **{s5['strict_schema_po']!r}**")
    w(f"- Nullable schema, validator rule demanding a PO: attempts returned "
      f"{[(a['po_number'], a['is_a_real_reference']) for a in s5['attempts']]} (value, is a real reference)")
    w(f"- Pipeline stopped without accepting an invented value: **{s5['stopped_without_accepting_invention']}**\n")
    w(f"> {s5['conclusion']}\n")

    if batch:
        w("## Stage 6 — Message Batches (optional)\n")
        if batch.get("timed_out_polling"):
            w(f"Batch `{batch['batch_id']}` was still processing when polling stopped; results remain retrievable by batch id.\n")
        else:
            w(f"- Batch `{batch['batch_id']}` ended in **{batch['seconds']}s**, {batch['succeeded']}/{len(DOCUMENTS)} succeeded")
            w(f"- Field accuracy: **{batch['score']['overall']['pct']}%** (same prompt and schema as stage 4)")
            w(f"- Failures to resubmit by `custom_id`: {batch['resubmit_only'] or 'none'}\n")
        w("Nobody is waiting on this path, which is the only reason it is allowed to be a batch; "
          "the synchronous stages above stay for the case where somebody is.\n")

    RUN_LOG.write_text("\n".join(out))
    log(f"\nwrote {RUN_LOG.relative_to(REPO_ROOT)}")


def main() -> None:
    want_batch = "--batch" in sys.argv
    log(f"Exercise 3 — structured extraction, model {MODEL}, {len(DOCUMENTS)} documents")

    log("\nStage 1 — 'respond only with JSON', no tool")
    s1 = stage1_prose()

    log("\nStage 2 — tool available, tool_choice auto")
    s2 = stage2_auto()

    log("\nStage 3 — forced tool, zero-shot, with validation-retry")
    zero = run_corpus(few_shot=False, tag="3")

    log("\nStage 4 — forced tool, three few-shot examples, with validation-retry")
    few = run_corpus(few_shot=True, tag="4")

    log("\nStage 5 — the unfixable field")
    s5 = stage5_unfixable()

    batch = None
    if want_batch:
        log("\nStage 6 — Message Batches")
        batch = stage6_batch()

    checks = build_checks(s1, s2, zero, few, s5)
    log("\nChecks:")
    for c in checks:
        log(f"  {'PASS' if c['pass'] else 'FAIL'}  {c['check']}")
    log(f"\n{usage_total['calls']} calls · {usage_total['input']:,} in · {usage_total['output']:,} out")

    write_log(s1, s2, zero, few, s5, checks, batch)
    RESULTS.write_text(json.dumps({
        "model": MODEL,
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "usage": usage_total,
        "stage1_prose": s1,
        "stage2_auto": s2,
        "stage3_zero_shot": zero,
        "stage4_few_shot": few,
        "stage5_unfixable": s5,
        "stage6_batch": batch,
        "checks": checks,
    }, indent=2, default=str))
    log(f"wrote {RESULTS.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
