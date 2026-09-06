"""
Exercise 36 — prompt caching in action.

Course C, section: "Prompt caching in action" (Features of Claude block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287774
    Code from the official 003_caching.ipynb — a starter whose chat() has
    two TODOs ("always cache tools", "always cache the system prompt");
    the lesson's clone-and-mark snippets complete them here. The ~6k
    system prompt and ~1.7k tool schemas live VERBATIM in
    caching_payload.py (course scaffolding, unedited).

WHAT THIS TEACHES
    A cache_control marker — {"type": "ephemeral"} on the LAST tool and on
    the system text block — makes the API store everything up to that
    point. Three usage fields tell the whole story:
        input_tokens                = the UNCACHED remainder only
        cache_creation_input_tokens = written this request (1.25x price)
        cache_read_input_tokens     = served from cache (0.1x price)
    Total prompt = the SUM of all three. Render order is tools -> system
    -> messages, and invalidation cascades FORWARD: change the system
    prompt and the tools cache still reads; change a tool and everything
    after it rewrites. One changed byte anywhere in a cached span
    invalidates that span and all spans after it.

EXAM LINK
    D5 — THE cost/latency lever for agent loops: the growing history from
    1.7 is resent every turn, and caching is what makes that affordable.
    D1 — same mechanism Claude Code relies on; a loop that rewrites its
    prefix (timestamps in the system prompt) silently pays full price
    every turn. The usage fields are the detector.

DIVERGENCES
    - THE LESSON'S TTL IS WRONG for the code it shows: "a cache that lives
      for one hour" — plain {"type": "ephemeral"} is the 5-MINUTE cache
      (each read refreshes the timer; requests <5 min apart keep it warm
      indefinitely). The 1-hour cache is opt-in — {"type": "ephemeral",
      "ttl": "1h"} — at 2x write price instead of 1.25x. Verified live:
      usage.cache_creation reports the write under ephemeral_5m_input_tokens.
    - Minimum cacheable prefix is model-dependent and SILENT on failure:
      1024 tokens on claude-sonnet-4-5 (this file clears it), but 4096 on
      claude-haiku-4-5 — the course's usual model would need a bigger
      payload before caching does anything at all.
    - Notebook chat() still passes temperature (SDK 1.2.0, ex. 06 row).

RUN
    From the repo root (five calls, ~1 minute; run twice within 5 minutes
    and stage 2's FIRST call becomes a read too — the previous run's cache):
        .venv/bin/python academy/course-c-claude-api/exercises/36-prompt-caching.py

    MEASURED 6 Sep 2026, claude-sonnet-4-5:
        uncached:            input=8433  write=0     read=0     1.7s
        request 1 (marked):  input=328   write=8105  read=0     1.9s
            usage.cache_creation: 5m=8105, 1h=0
            -> THE DIVERGENCE, PROVEN: the lesson's code buys the
               5-MINUTE cache, not the "one hour" the lesson claims.
        request 2:           input=328   write=0     read=8105  2.1s
        one-char system edit:input=329   write=6333  read=1773  2.2s
            -> the promised partial hit, exact: 1773 read = the TOOLS
               span (lesson said ~1.7k), 6333 rewritten = the system
               span. Tools render before system, so the edit only
               invalidated forward.
        repeat of the edit:  input=329   write=0     read=8106
        Totals identical every time (8433/8435): input_tokens is only
        the UNCACHED REMAINDER — the question (328) — never the prompt
        size. Economics at these numbers: steady-state repeat costs
        328 + 8105x0.1 ~= 1,139 token-equivalents vs 8,433 uncached —
        ~86% off every request after the first. Latency was FLAT
        (1.7s vs ~2s) — at 8k tokens the win is money, not speed;
        latency gains need much larger prefixes.
"""

import time

from anthropic import Anthropic
from dotenv import load_dotenv

from caching_payload import (
    add_duration_to_datetime_schema,
    code_prompt,
    db_query_schema,
    get_current_datetime_schema,
    set_reminder_schema,
)

load_dotenv()

client = Anthropic()

MODEL = "claude-sonnet-4-5"

TOOLS = [
    db_query_schema,
    add_duration_to_datetime_schema,
    set_reminder_schema,
    get_current_datetime_schema,
]


# ---------------------------------------------------------------- helpers
def add_user_message(messages, message):
    content = message if isinstance(message, list) else [
        {"type": "text", "text": message}
    ]
    messages.append({"role": "user", "content": content})


def chat(messages, system=None, tools=None, cache=True):
    """The notebook's chat() with its two TODOs completed by the lesson's
    snippets. cache=False is our toggle so stage 1 can show the baseline."""
    params = {"model": MODEL, "max_tokens": 4000, "messages": messages}

    if tools:
        if cache:
            # Lesson: clone list and last tool, mark the LAST tool — the
            # marker caches everything up to and including that point.
            tools_clone = tools.copy()
            last_tool = tools_clone[-1].copy()
            last_tool["cache_control"] = {"type": "ephemeral"}
            tools_clone[-1] = last_tool
            params["tools"] = tools_clone
        else:
            params["tools"] = tools

    if system:
        if cache:
            # Lesson: string -> text block carrying the marker.
            params["system"] = [{
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            }]
        else:
            params["system"] = system

    return client.messages.create(**params)


def call(question, system, cache=True, label=""):
    messages = []
    add_user_message(messages, question)
    t0 = time.perf_counter()
    response = chat(messages, system=system, tools=TOOLS, cache=cache)
    elapsed = time.perf_counter() - t0
    u = response.usage
    total = u.input_tokens + u.cache_creation_input_tokens + u.cache_read_input_tokens
    print(f"{label:<28} input={u.input_tokens:<6} "
          f"cache_write={u.cache_creation_input_tokens:<6} "
          f"cache_read={u.cache_read_input_tokens:<6} "
          f"total={total:<6} {elapsed:.1f}s")
    return response


QUESTION = "what's 1+1"        # the notebook's question — the payload is
                               # the prompt, not the task

# -------------------------------------------------- stage 1: the baseline
print("=" * 76)
print("STAGE 1 — no markers: the full ~7.7k prompt is billed as input, every time")
print("=" * 76)
call(QUESTION, code_prompt, cache=False, label="uncached")

# ------------------------------- stage 2: write once, read on the repeat
print()
print("=" * 76)
print("STAGE 2 — markers on last tool + system: first request WRITES, repeat READS")
print("=" * 76)
r = call(QUESTION, code_prompt, label="request 1 (expect write)")
breakdown = r.usage.cache_creation
if breakdown:
    print(f"{'':28} usage.cache_creation: 5m={breakdown.ephemeral_5m_input_tokens} "
          f"1h={breakdown.ephemeral_1h_input_tokens}  <- WHICH cache the lesson's "
          f"code actually buys")
call(QUESTION, code_prompt, label="request 2 (expect read)")

# --------------- stage 3: change ONE character in the system prompt only
# Order is tools -> system -> messages. The tools span is untouched, so it
# should READ; the system span changed, so it (alone) rewrites.
print()
print("=" * 76)
print("STAGE 3 — one-char system edit: tools still READ, only system re-WRITES")
print("=" * 76)
call(QUESTION, code_prompt + "!", label="edited system prompt")
call(QUESTION, code_prompt + "!", label="repeat of the edit")

# NOTES FROM THE COURSE
# - Mark the LAST tool (clone first — mutating tools[-1] in place goes
#   wrong the day the list is reordered) and the system text block.
# - First request: cache_creation_input_tokens. Follow-ups:
#   cache_read_input_tokens. Change a component and its span re-writes
#   while spans BEFORE it keep reading — pay only for what changed.
# - Byte-sensitive: one character anywhere in the span is a full re-write
#   of that span and everything after it.
# - Worth caching when tool schemas and system prompts are stable and
#   requests are frequent: exactly an agent loop's shape.
#
# WORTH KNOWING (current API, D5)
# - Up to 4 breakpoints per request; messages can carry one too — in an
#   agent loop, mark the last message and move the marker forward each
#   turn so history reads from cache (growth is append-only).
# - The economics: read 0.1x, write 1.25x (5m) — two requests already
#   break even. The 1h cache writes at 2x and only pays off when gaps
#   between requests are 5-60 minutes.
# - Verify with cache_read_input_tokens, not vibes: a datetime.now() in
#   the system prompt, unsorted JSON, or a varying tool list all
#   invalidate SILENTLY — the only symptom is reads stuck at zero while
#   writes recur every request.
