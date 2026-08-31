"""
Exercise 09 — structured data exercise (the slide task).

Course C, section: "Structured data" — the practice slide.
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287732

THE BRIEF
    - Use message prefilling and stop sequences ONLY to get three different
      commands in a single response
    - There shouldn't be any comments or explanation
    - Hint: message prefilling isn't limited to just characters like ```

    Starting point given on the slide:
        messages = []
        prompt = "Generate three different sample AWS CLI commands. Each should be very short."
        add_user_message(messages, prompt)
        text = chat(messages)
        text.strip()

THE REASONING
    A prefill works by making Claude believe it is already mid-format, so it
    continues in that format instead of introducing one. The stop sequence then
    ends generation at whatever marker would come next.

    Two prefills were tried, and the choice matters more than it looks:

      "1. aws" + stop ["4."]
          A numbered list. The stop fires when a FOURTH item begins, so it
          caps the count at three. Output needs the "N. " prefixes stripped.

      "Here are all the three commands...\n```bash" + stop ["```"]
          A fenced block. Commands come out bare and directly runnable, but
          the stop only fires at the CLOSING fence — which arrives after every
          command. It does NOT cap the count. Stage 2 proves this.

    So format cleanliness and length enforcement are separate wins, and these
    two prefills each buy only one of them.

*** PREFILL IS REMOVED ON CURRENT MODELS ***
    The brief mandates prefill, so the solution runs on a dated snapshot.
    On claude-opus-5 it is a 400: "This model does not support assistant
    message prefill." Stage 3 gives the modern equivalent. See exercise 08.

EXAM LINK (Domain 4)
    Note which part actually guarantees the constraint. The prompt says
    "three"; the model complying is a request being honoured, not enforced.
    Whether the stop sequence enforces anything depends on the marker you
    stop at: "4." bounds the count, "```" bounds only the block. Stage 2
    asks for TEN to show which is which.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/09-structured-data-exercise.py
"""

import json

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-opus-5"
LEGACY_MODEL = "claude-sonnet-4-5-20250929"      # still accepts assistant prefill

PROMPT = "Generate three different sample AWS CLI commands. Each should be very short."
# The hint says prefilling is not limited to characters like ```. Two prefills
# were tried, and they enforce DIFFERENT things — see stage 2.
#   "1. aws"  + stop ["4."]  -> numbered list; the stop caps the COUNT at three
#   "...```bash" + stop ["```"] -> fenced block; the stop only ends the BLOCK,
#                                 so the count is not capped, but the commands
#                                 come out bare and directly runnable.
PREFILL = "Here are all the three commands without any comments:\n```bash"
STOP = ["```"]            # fires at the CLOSING fence — ends the block, not the list


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, content):
    messages.append({"role": "assistant", "content": content})


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


# =====================================================================
print("=" * 70)
print("STAGE 1 — the solution")
print("=" * 70)

messages = []
add_user_message(messages, PROMPT)
add_assistant_message(messages, PREFILL)

answer = client.messages.create(
    model=LEGACY_MODEL, max_tokens=400, messages=messages, stop_sequences=STOP
)
returned = text_of(answer)

print(f"prefill sent:  {PREFILL!r}")
print(f"stop sequence: {STOP}")
print(f"stop_reason:   {answer.stop_reason}")
print()
print(f"what the API returned (note: the prefill is NOT echoed back):")
print(f"  {returned!r}")
print()

# Do NOT reassemble prefill + returned here. This prefill contains a SENTENCE,
# and prepending it puts commentary back into the output — the exact thing the
# brief forbids. With a fenced prefill the clean payload is `returned` alone.
print("the clean payload — `returned` on its own:")
for line in returned.strip().split("\n"):
    print(f"  |{line}")
print()
print("for contrast, prefill + returned would reintroduce the preamble:")
print(f"  |{PREFILL.splitlines()[0]}")
print("  |... which is commentary, and the brief forbids it.")
print()

# Bare lines now, not "N. command" — this prefill produces no numbering.
commands = [ln.strip() for ln in returned.strip().split("\n") if ln.strip()]
print(f"parsed {len(commands)} commands, no commentary:")
for cmd in commands:
    print(f"  $ {cmd}")
print()


# =====================================================================
print("=" * 70)
print("STAGE 2 — does the stop sequence actually enforce 'three'?")
print("=" * 70)
print(f"Stage 1 ended with stop_reason={answer.stop_reason!r}: the closing fence")
print("fired the stop. But did that CAP the list, or merely end the block after")
print("the model had already finished? Ask for ten and find out:")
print()

messages = []
add_user_message(messages, "Generate ten different sample AWS CLI commands. Each should be very short.")
add_assistant_message(messages, PREFILL)

capped = client.messages.create(
    model=LEGACY_MODEL, max_tokens=400, messages=messages, stop_sequences=STOP
)
capped_commands = [ln.strip() for ln in text_of(capped).strip().split("\n") if ln.strip()]
print(f"prompt asked for TEN | stop_reason={capped.stop_reason} | "
      f"got {len(capped_commands)} commands")
for cmd in capped_commands:
    print(f"  $ {cmd}")
print()
if len(capped_commands) > 3:
    print("More than three. The ``` stop did NOT cap the count — it fired at the")
    print("closing fence, which the model only writes AFTER finishing every item.")
    print()
    print("Compare the numbered-list prefill: \"1. aws\" with stop [\"4.\"] returns")
    print("exactly three even when asked for ten, because the stop marker is what")
    print("a FOURTH item starts with. Verified 31 Aug 2026.")
    print()
    print("Lesson: a stop sequence enforces a bound only if the marker you choose")
    print("appears at the point you want to stop. Choosing ``` bounds the block;")
    print("choosing \"4.\" bounds the list.")
else:
    print("Three or fewer — but that is the model complying with the prompt, not")
    print("the fence enforcing a bound. Re-run: this outcome is not reliable.")
print()


# =====================================================================
print("=" * 70)
print("STAGE 3 — the same brief on a current model")
print("=" * 70)

messages = []
add_user_message(messages, PROMPT)
add_assistant_message(messages, PREFILL)
try:
    client.messages.create(model=MODEL, max_tokens=400, messages=messages, stop_sequences=STOP)
    print("no error raised")
except Exception as exc:
    detail = getattr(getattr(exc, "body", None), "get", lambda _k, _d=None: None)("error") or {}
    msg = detail.get("message") if isinstance(detail, dict) else None
    print(f"{type(exc).__name__}: {msg or str(exc)[:150]}")
print()

print("The modern equivalent — but read what the schema can and cannot do:")
print()

# minItems > 1 and maxItems are BOTH rejected by strict schemas. Verified:
#   minItems=3        -> 400 "'minItems' values other than 0 or 1 are not supported"
#   maxItems=3        -> 400 "property 'maxItems' is not supported"
# So a schema CANNOT pin the count. It pins the shape.
SCHEMA = {
    "type": "object",
    "properties": {
        "commands": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["commands"],
    "additionalProperties": False,
}

WANT = 3


def ask_for_commands(n_requested):
    r = client.messages.create(
        model=MODEL, max_tokens=1000,
        output_config={"format": {"type": "json_schema", "schema": SCHEMA}},
        messages=[{"role": "user", "content":
                   f"Generate {n_requested} different sample AWS CLI commands. "
                   f"Each should be very short."}],
    )
    return json.loads(text_of(r))["commands"]


got = ask_for_commands("ten")
print(f"  schema with no count constraint, prompt asked for TEN -> {len(got)} items")
print("  The shape is guaranteed. The COUNT is not — the schema cannot express it.")
print()

print("  Rejected by strict schemas (verified 31 Aug 2026):")
print("    minItems=3   400 \"'minItems' values other than 0 or 1 are not supported\"")
print("    maxItems=3   400 \"property 'maxItems' is not supported\"")
print()

print(f"  So to GUARANTEE exactly {WANT}, validate in code and retry — Domain 4.4:")
for attempt in range(1, 4):
    commands = ask_for_commands(WANT)
    if len(commands) == WANT:
        print(f"    attempt {attempt}: {len(commands)} items — accepted")
        break
    print(f"    attempt {attempt}: {len(commands)} items — rejected, retrying")
else:
    commands = commands[:WANT]
    print(f"    exhausted retries; truncated to {WANT}")

for cmd in commands:
    print(f"  $ {cmd}")
print()

print("=" * 70)
print("WHAT ACTUALLY GUARANTEES WHAT")
print("=" * 70)
print("  prompt says 'three'          a REQUEST     — usually honoured")
print("  prefill (either kind)        FORMAT        — removed on current models")
print("  stop_sequences ['4.']        LENGTH        — bounds the list; still works")
print("  stop_sequences ['```']       BLOCK END     — bounds the fence, NOT the count")
print("  json_schema                  SHAPE         — types, keys, no extras")
print("  code validation + retry      EVERYTHING    — the only real guarantee")
print()
print("Neither mechanism is complete on its own. That is the Domain 4 lesson:")
print("push what you can into the schema, then verify the rest in code.")

# NOTES FROM THE COURSE
# - The hint is the whole exercise: prefill any text that puts Claude mid-format,
#   not just a code fence. A list marker ("1. aws") works because it implies
#   "2." and "3." follow in the same bare style. A fenced prefill
#   ("...\n```bash") works because everything inside a bash fence is a command.
# - Prefill sets the FORMAT. The stop sequence sets the BOUND — but only if the
#   marker sits where you want the bound. See trap 5.
#
# TRAPS FOUND WHILE SOLVING THIS, all verified 31 Aug 2026
# 1. A prefill may not end with whitespace:
#      400 "messages: final assistant content cannot end with trailing whitespace"
#    So "1. aws " fails and "1. aws" works.
# 2. The prefill is NOT echoed in the response. The API returns only the
#    continuation, so reconstruct with prefill + returned_text.
# 3. Prefilling just "1." is not enough — the model still produced bold headings
#    and ```bash fences, breaking the "no explanation" requirement. Prefilling
#    "1. aws" carries the bare-command style into every item.
# 4. A prefill containing a SENTENCE (as this one does) must not be prepended to
#    the output. Reassembling prefill + response puts the preamble back in and
#    breaks the "no comments or explanation" rule. Use the returned text alone.
# 5. The stop marker decides WHAT is bounded, and this is easy to get wrong:
#      stop ["4."]   fires where a fourth list item would begin -> caps the COUNT
#      stop ["```"]  fires at the closing fence, written only AFTER every item
#                    -> caps nothing; asking for ten returns ten
#    Both give stop_reason="stop_sequence", so the stop_reason alone does not
#    tell you whether your bound worked. Check the content.
#
# DIVERGENCE
# 5. Assistant prefill is removed on current models (400) — this whole brief is
#    unrunnable on claude-opus-5.
# 6. Structured outputs are NOT a complete replacement. They enforce SHAPE but
#    cannot express CARDINALITY: strict schemas reject maxItems entirely, and
#    reject minItems above 1. So "exactly three" cannot be a schema constraint.
#    The deterministic answer is schema for shape + a length check in code with
#    a retry — which is Domain 4.4, validation and retry.
