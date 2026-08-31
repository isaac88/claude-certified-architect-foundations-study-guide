"""
Exercise 08 — structured data.

Course C, section: "Structured data".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287732

THE PROBLEM
    Ask for JSON and Claude helpfully wraps it: a markdown ```json fence, and
    a sentence of explanation afterwards. For a web app whose users click
    "generate" and copy the result, that wrapping is friction.

THE LESSON'S SOLUTION
    Assistant-message prefilling plus a stop sequence:
        add_user_message(messages, "Generate a very short event bridge rule as json")
        add_assistant_message(messages, "```json")
        text = chat(messages, stop_sequences=["```"])
    Claude believes it already opened a code fence, so it continues with just
    the JSON; the moment it tries to close the fence, the stop sequence ends
    generation.

*** THE BIG DIVERGENCE ***
    Assistant prefill is REMOVED on current models. Verified 31 Aug 2026:
        claude-opus-5 + prefill -> 400
        "This model does not support assistant message prefill.
         The conversation must end with a user message"
    Precisely what changed:
      - prefill            REMOVED on current models (400)
      - stop_sequences     still supported, works fine
      - dated snapshots    still accept the full technique
    Stage 2 therefore demonstrates the lesson on claude-sonnet-4-5-20250929,
    stage 3 shows the 400 on a current model, and stage 4 gives the modern
    replacement: structured outputs.

EXAM LINK (Domain 4)
    "Get clean structured output" is a Domain 4 task statement. The scoring
    habit is deterministic over probabilistic: a prompt asking nicely for
    "JSON only" is a request, a schema-constrained response is a guarantee.
    Prefill-plus-stop-sequence sat in between — a clever hack around a
    formatting problem the API now solves properly.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/08-structured-data.py
"""

import json

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-opus-5"
LEGACY_MODEL = "claude-sonnet-4-5-20250929"   # still accepts assistant prefill

ASK = "Generate a very short event bridge rule as json"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, content):
    messages.append({"role": "assistant", "content": content})


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


# =====================================================================
print("=" * 70)
print("STAGE 1 — the problem: Claude wraps what you asked for")
print("=" * 70)

messages = []
add_user_message(messages, ASK)
plain = client.messages.create(model=MODEL, max_tokens=1000, messages=messages)
raw = text_of(plain)

print(raw)
print()
print("--- is that directly parseable? ---")
try:
    json.loads(raw)
    print("  json.loads() succeeded")
except json.JSONDecodeError as exc:
    print(f"  json.JSONDecodeError: {exc}")
    print("  -> a user cannot copy the whole response; a program cannot parse it")
print()

# =====================================================================
print("=" * 70)
print(f"STAGE 2 — the lesson's technique, working, on {LEGACY_MODEL}")
print("=" * 70)

messages = []
add_user_message(messages, ASK)
add_assistant_message(messages, "```json")        # <- the prefill

legacy = client.messages.create(
    model=LEGACY_MODEL,
    max_tokens=1000,
    messages=messages,
    stop_sequences=["```"],                        # <- ends generation at the fence
)
prefilled = text_of(legacy)

print(f"stop_reason: {legacy.stop_reason}")
print(f"raw repr:    {prefilled[:60]!r} ...")
print()
print("--- after .strip() and json.loads() ---")
try:
    parsed = json.loads(prefilled.strip())
    print(json.dumps(parsed, indent=2))
    print("  parsed cleanly")
except json.JSONDecodeError as exc:
    print(f"  json.JSONDecodeError: {exc}")
print()
print("Note stop_reason is 'stop_sequence', not 'end_turn'. The model was cut")
print("off deliberately — it never finished its turn. Do not treat that as a")
print("completed response in a loop (see Domain 1.1).")
print()


# =====================================================================
print("=" * 70)
print("STAGE 3 — the identical code against a current model")
print("=" * 70)

messages = []
add_user_message(messages, ASK)
add_assistant_message(messages, "```json")

try:
    client.messages.create(
        model=MODEL, max_tokens=1000, messages=messages, stop_sequences=["```"]
    )
    print("no error raised")
except Exception as exc:
    detail = getattr(getattr(exc, "body", None), "get", lambda _k, _d=None: None)("error") or {}
    msg = detail.get("message") if isinstance(detail, dict) else None
    print(f"{type(exc).__name__}: {msg or str(exc)[:160]}")
print()
print("What exactly is gone — verified separately:")
print("  prefill                    REMOVED on current models (400)")
print("  stop_sequences alone       still works")
print("  dated snapshots            still accept prefill")
print()
print("So it is prefill that was removed, not stop sequences. Proof that")
print("stop_sequences still works on a current model:")
probe = client.messages.create(
    model=MODEL, max_tokens=500,          # thinking spends budget before any text
    messages=[{"role": "user", "content":
               "Output only the numbers 1 to 10 separated by spaces. No other text."}],
    stop_sequences=["5"],                 # a token the answer must contain
)
print(f"  stop_reason={probe.stop_reason}  text={text_of(probe)!r}")
if probe.stop_reason == "max_tokens":
    print("  (starved: thinking consumed max_tokens before text began — raise it)")
print()

# =====================================================================
print("=" * 70)
print("STAGE 4 — the modern replacement: structured outputs")
print("=" * 70)

# NOTE a strict-schema rule found the hard way: EVERY object needs
# "additionalProperties": False — nested ones included. Leaving it off the
# inner "detail" object returns:
#   400 output_config.format.schema: For 'object' type,
#       'additionalProperties' must be explicitly set to false
RULE_SCHEMA = {
    "type": "object",
    "properties": {
        "source": {"type": "array", "items": {"type": "string"}},
        "detail-type": {"type": "array", "items": {"type": "string"}},
        "detail": {
            "type": "object",
            "properties": {
                "state": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["state"],
            "additionalProperties": False,      # <- required on nested objects too
        },
    },
    "required": ["source", "detail-type", "detail"],
    "additionalProperties": False,
}

messages = []
add_user_message(messages, ASK)

structured = client.messages.create(
    model=MODEL,
    max_tokens=1000,
    output_config={"format": {"type": "json_schema", "schema": RULE_SCHEMA}},
    messages=messages,
)
out = text_of(structured)

print(f"stop_reason: {structured.stop_reason}")
print(f"raw:         {out!r}")
print()
print("--- parse it ---")
parsed = json.loads(out)
print(json.dumps(parsed, indent=2))
print()
print("No prefill. No stop sequence. No fence to strip, no prose to cut, and")
print("no ambiguity about which of two code blocks was meant. The shape is")
print("guaranteed by the schema rather than requested in prose.")
print()

print("--- schema violations are impossible, not merely unlikely ---")
print(f"keys returned:   {sorted(parsed)}")
print(f"schema required: {sorted(RULE_SCHEMA['required'])}")
print(f"additionalProperties: False -> no unexpected keys can appear")
print()

print("=" * 70)
print("SUMMARY — three ways to get clean JSON, in order of strength")
print("=" * 70)
print("  1. Ask nicely in the prompt        a REQUEST. Model may still wrap it.")
print("  2. Prefill + stop_sequence         a HACK. Worked; prefill now 400s.")
print("  3. output_config.format schema     a GUARANTEE of SHAPE. Use this.")
print("  4. schema + validation in code      a guarantee of everything else")
print("     (schemas cannot express counts — see exercise 09)")
print()
print("Domain 4's habit in one line: prefer the guarantee to the request.")

# NOTES FROM THE COURSE
# - Claude wraps generated data in markdown and commentary because that is
#   usually helpful. For machine consumption it is friction.
# - The prefill trick works by making Claude believe it already opened a fence,
#   so it continues with content; the stop sequence cuts it at the closing one.
# - Watch stop_reason with stop sequences: it is "stop_sequence", NOT
#   "end_turn". The turn was cut short deliberately (relevant to Domain 1.1 —
#   do not treat a cut-off turn as a completed one).
# - The technique generalises beyond JSON: Python, CSV, bulleted lists. Prefill
#   whatever wrapper the model would otherwise add.
#
# DIVERGENCES, verified 31 Aug 2026
# 1. Assistant prefill is REMOVED on current models:
#      400 "This model does not support assistant message prefill.
#           The conversation must end with a user message."
#    Isolated by testing: prefill alone 400s; stop_sequences alone is fine;
#    dated snapshots (claude-sonnet-4-5-20250929) still accept prefill.
# 2. The replacement is structured outputs:
#      output_config={"format": {"type": "json_schema", "schema": {...}}}
#    Returns bare JSON — no fence, no preamble, nothing to strip. Shape is
#    enforced rather than requested.
#    CAVEAT (found in exercise 09): schemas enforce shape, NOT cardinality.
#    Strict schemas reject maxItems outright and reject minItems above 1, so
#    "exactly three items" cannot be a schema constraint. Push shape into the
#    schema, then verify counts in code.
# 3. Strict schemas require "additionalProperties": False on EVERY object in
#    the schema, nested ones included, or:
#      400 output_config.format.schema: For 'object' type,
#          'additionalProperties' must be explicitly set to false
# 4. A trap found while writing this file: with thinking on by default, a small
#    max_tokens can be consumed entirely by reasoning, returning
#    stop_reason="max_tokens" and an EMPTY text block. If a response comes back
#    empty, check whether the budget was starved before blaming the prompt.
