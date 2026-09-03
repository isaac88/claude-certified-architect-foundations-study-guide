"""
Exercise 32 — extended thinking.

Course C, section: "Extended thinking" (Features of Claude block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287773

WHAT THIS TEACHES
    Extended thinking gives the model scratch paper BEFORE the answer: the
    response gains a `thinking` block ahead of the `text` block. You buy
    better reasoning with two currencies — thinking tokens are billed as
    output, and generation takes longer. The lesson's rule for WHEN: run
    your evals without thinking first; enable it only when an optimised
    prompt still misses the accuracy bar.

    Two response details the loop must handle:
    - Every `thinking` block carries a cryptographic `signature` proving
      the reasoning text was not tampered with before being passed back.
    - Sometimes the reasoning arrives as a `redacted_thinking` block —
      encrypted `data`, no readable text. Pass it back UNCHANGED in
      multi-turn history; context survives even though you cannot read it.

EXAM LINK
    D4 — "should I enable thinking?" is an eval question, not a vibes
    question: measure without it, optimise the prompt, then re-measure.
    D5 — a features decision with explicit cost + latency trade-offs, and
    a response shape (`content[0]` is NOT text) that re-breaks any loop
    still indexing by position (the exercise-02 lesson, third appearance).

DIVERGENCES
    - The lesson page writes the config as {"type": "enabled",
      "budget": thinking_budget}. The real parameter is `budget_tokens` —
      `budget` is rejected. Recorded in the README divergence table.
    - The lesson's chat() keeps temperature=1.0; sampling params are gone
      from SDK 1.2.0 (exercise 06), so the helper here has no temperature.
      The docs' thinking restriction "temperature must be 1" is therefore
      unhittable from this SDK.
    - `budget_tokens` only exists on pre-4.6 models like this one. On the
      4.6+/5 families the whole concept is replaced by adaptive thinking
      ({"type": "adaptive"}) and sending budget_tokens is a 400.

RUN
    From the repo root (three short calls, ~30s):
        .venv/bin/python academy/course-c-claude-api/exercises/32-extended-thinking.py

    MEASURED 3 Sep 2026, claude-haiku-4-5:
        thinking OFF: blocks ['text'],             402 output tokens,  4.1s
        thinking ON:  blocks ['thinking', 'text'], 1797 output tokens, 16.1s
            -> same question, ~4.5x the output tokens and ~4x the wall
               clock. The budget (2048) is a ceiling, not a target: the
               thinking text was ~2.2k chars, well under it.
            -> signature was 4332 chars — bigger than the thinking text
               it signs.
        redacted trigger: blocks ['redacted_thinking', 'text'] — the
            handling path ran without crashing (1256 chars of encrypted
            data). The keeper: the model's VISIBLE text claimed the magic
            string "is not a real command and doesn't trigger any special
            behavior" — while the redacted block it triggered sat directly
            above that sentence. Trust the wire, not the self-report.
        lesson's "budget" key, tested live:
            400 "thinking.enabled.budget_tokens: Field required"
"""

import time

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-haiku-4-5"

# Documented trigger string that forces a redacted_thinking block, so the
# handling path can be tested without waiting for a real safety flag.
REDACTED_TRIGGER = (
    "ANTHROPIC_MAGIC_STRING_TRIGGER_REDACTED_THINKING_46C9A13E193C177646C7"
    "398A98432ECCCE4C1253D5E2D82641AC0E52CC2876CB"
)


# ---------------------------------------------------------------- helpers
def add_user_message(messages, message):
    messages.append({"role": "user", "content": message})


def chat(messages, system=None, stop_sequences=[], tools=None,
         thinking=False, thinking_budget=1024):
    # The lesson's two new params. Rules: budget minimum is 1024, and
    # max_tokens must be GREATER than the budget or the request 400s —
    # the final answer has to fit in what the budget leaves over.
    params = {
        "model": MODEL,
        "max_tokens": 4000,
        "messages": messages,
        "stop_sequences": stop_sequences,
    }
    if system:
        params["system"] = system
    if tools:
        params["tools"] = tools
    if thinking:
        params["thinking"] = {
            "type": "enabled",
            "budget_tokens": thinking_budget,   # lesson page says "budget" — 400s
        }
    return client.messages.create(**params)


def show_response(response, elapsed):
    """Print every block BY TYPE — with thinking on, content[0] is not text."""
    print(f"blocks: {[b.type for b in response.content]}")
    for block in response.content:
        if block.type == "thinking":
            preview = " ".join(block.thinking.split())[:300]
            print(f"\n[thinking] ({len(block.thinking)} chars) {preview}...")
            print(f"[signature] {block.signature[:60]}... "
                  f"({len(block.signature)} chars)")
        elif block.type == "redacted_thinking":
            print(f"\n[redacted_thinking] no readable text; encrypted data, "
                  f"{len(block.data)} chars — pass back unchanged in history")
        elif block.type == "text":
            print(f"\n[text] {block.text.strip()[:400]}")
    print(f"\nstop_reason={response.stop_reason}  "
          f"output_tokens={response.usage.output_tokens}  "
          f"elapsed={elapsed:.1f}s")


QUESTION = (
    "A batch job processes 10,000 records. Each record takes 2 seconds on "
    "one worker. Workers cost $0.10 per hour each, and adding a worker adds "
    "30 seconds of one-off startup time. The job must finish within 1 hour. "
    "What is the cheapest number of workers, and what does the job cost?"
)

# ------------------------------------ stage 1: same question, without/with
print("=" * 70)
print("STAGE 1 — the same question, thinking OFF then ON")
print("=" * 70)

print("\n--- thinking OFF ---")
messages = []
add_user_message(messages, QUESTION)
t0 = time.perf_counter()
response_off = chat(messages)
show_response(response_off, time.perf_counter() - t0)

print("\n--- thinking ON (budget 2048) ---")
messages = []
add_user_message(messages, QUESTION)
t0 = time.perf_counter()
response_on = chat(messages, thinking=True, thinking_budget=2048)
show_response(response_on, time.perf_counter() - t0)

print("\nThe trade in numbers: output_tokens "
      f"{response_off.usage.output_tokens} -> {response_on.usage.output_tokens} "
      "(thinking tokens are BILLED as output; the budget is a ceiling, "
      "not a target).")

# --------------------------------------- stage 2: redacted thinking, forced
# A flagged thought arrives encrypted. The client's job is graceful
# handling: recognise the block type, do not crash, do not drop it.
print()
print("=" * 70)
print("STAGE 2 — forcing a redacted_thinking block (the magic string)")
print("=" * 70)
messages = []
add_user_message(messages, REDACTED_TRIGGER)
t0 = time.perf_counter()
response_redacted = chat(messages, thinking=True)
show_response(response_redacted, time.perf_counter() - t0)

# NOTES FROM THE COURSE
# - Response with thinking on = thinking block(s) + text block. Benefits:
#   better reasoning, accuracy, transparency. Costs: tokens, latency, more
#   complex response handling.
# - WHEN to enable: prompt evals first. Optimise the prompt; if accuracy
#   still short, THEN add thinking. It is not a default.
# - signature = cryptographic token proving the thinking text is unmodified
#   — tampered reasoning cannot be replayed into the model.
# - redacted_thinking = safety-flagged reasoning, encrypted in `data`.
#   Passing the complete message back keeps the context without exposing
#   the content. Test your handling with the magic string, not by hoping.
# - budget minimum 1024; max_tokens must exceed the budget.
# - Feature compatibility: no prefill and no temperature changes alongside
#   thinking (docs list); both are moot on SDK 1.2.0 / current models.
#
# WORTH KNOWING (current API)
# - This budget dial is generation N-1: on 4.6+/5 models thinking is
#   adaptive ({"type": "adaptive"} — the model decides when and how much)
#   and `budget_tokens` returns a 400. The depth lever there is
#   output_config.effort. Same architecture question, new knob.
# - Exercise 02's divergence row was THIS feature seen from the other side:
#   current models emit thinking blocks by default, which is exactly why
#   content[0].text was already breaking before this lesson introduced
#   thinking at all.
