"""
Exercise 07 — response streaming.

Course C, section: "Response streaming".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287734

WHAT THIS TEACHES
    A non-streaming request returns nothing until the whole response is
    generated. Streaming returns a sequence of events as the text is
    produced, so a user sees words appearing instead of a spinner.

    Same single HTTP request either way — streaming changes how the response
    body is delivered, not how many calls you make.

THE JOURNEY
    1. Measure the problem — time to first visible output, both ways.
    2. Look at the raw events (`stream=True`), and learn their real names.
    3. Use the SDK's `text_stream` helper for just the text.
    4. Recover the complete message with `get_final_message()` for storage.
    5. What `text_stream` hides, and when streaming stops being optional.

MEASURED (31 Aug 2026, claude-opus-5, ~150-word answer)
    no streaming: first output at 6.87s, complete at 6.87s
    streaming:    first output at 3.29s, complete at 8.70s
    Total wall time is comparable; time to first output roughly halves. That
    is the entire user-experience argument, and it is worth noting streaming
    finished slightly LATER overall — you trade a little throughput for a lot
    of perceived responsiveness.

EXAM LINK (Domain 5)
    Streaming is a UX and reliability concern, not a capability one. It is
    also mandatory rather than optional at large `max_tokens`: a big
    non-streaming request can exceed the HTTP timeout and fail outright.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/07-response-streaming.py
"""

import time

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-opus-5"

PROMPT = "Write a 1 sentence description of a fake database."
LONGER = "Explain how a B-tree index works, in about 150 words."


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


# =====================================================================
print("=" * 70)
print("STAGE 1 — measure the problem: when does the user see anything?")
print("=" * 70)

messages = []
add_user_message(messages, LONGER)

# --- without streaming
t0 = time.perf_counter()
blocking = client.messages.create(model=MODEL, max_tokens=1000, messages=messages)
blocking_first = blocking_total = time.perf_counter() - t0
print(f"  no streaming: first output after {blocking_first:5.2f}s, complete at {blocking_total:5.2f}s")

# --- with streaming
t0 = time.perf_counter()
stream_first = None
with client.messages.stream(model=MODEL, max_tokens=1000, messages=messages) as stream:
    for _ in stream.text_stream:
        if stream_first is None:
            stream_first = time.perf_counter() - t0
stream_total = time.perf_counter() - t0
print(f"  streaming:    first output after {stream_first:5.2f}s, complete at {stream_total:5.2f}s")
print()
print("  Total time is similar. Time to FIRST output is the whole point:")
print(f"  the user waits {blocking_first:.2f}s vs {stream_first:.2f}s before seeing anything.")
print()


# =====================================================================
print("=" * 70)
print("STAGE 2 — the raw events, and their real names")
print("=" * 70)

messages = []
add_user_message(messages, PROMPT)

raw = client.messages.create(model=MODEL, max_tokens=1000, messages=messages, stream=True)

counts = {}
order = []
for event in raw:
    counts[event.type] = counts.get(event.type, 0) + 1
    if event.type not in order:
        order.append(event.type)

print("  first occurrence, in order:")
for name in order:
    print(f"    {name:26} x{counts[name]}")
print()
print("  The course lists these as MessageStart / ContentBlockDelta / etc.")
print("  On the wire they are snake_case, as printed above. Note also the")
print("  delta SUBtypes: a content_block_delta carries a text_delta, or a")
print("  thinking_delta, or an input_json_delta for tool arguments.")
print()


# =====================================================================
print("=" * 70)
print("STAGE 3 — text_stream: just the words")
print("=" * 70)
print("  (printed as it arrives, no buffering)\n")

messages = []
add_user_message(messages, PROMPT)

print("  ", end="", flush=True)
chunks = 0
with client.messages.stream(model=MODEL, max_tokens=1000, messages=messages) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
        chunks += 1
print(f"\n\n  arrived in {chunks} chunks")
print()


# =====================================================================
print("=" * 70)
print("STAGE 4 — get_final_message(): the complete object for storage")
print("=" * 70)

messages = []
add_user_message(messages, PROMPT)

with client.messages.stream(model=MODEL, max_tokens=1000, messages=messages) as stream:
    for _ in stream.text_stream:
        pass                      # in a real app: forward each chunk to the client
    final = stream.get_final_message()

print(f"  stop_reason: {final.stop_reason}")
print(f"  blocks:      {[b.type for b in final.content]}")
print(f"  usage:       {final.usage.input_tokens} in / {final.usage.output_tokens} out")
print()
print("  This is a normal Message object — the same shape a non-streaming call")
print("  returns. Append `final.content` to your history exactly as before.")
print()


# =====================================================================
print("=" * 70)
print("STAGE 5 — what text_stream hides, and when streaming is mandatory")
print("=" * 70)

messages = []
add_user_message(messages, LONGER)

kinds = {}
with client.messages.stream(model=MODEL, max_tokens=1000, messages=messages) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            kinds[event.delta.type] = kinds.get(event.delta.type, 0) + 1
    final = stream.get_final_message()

print("  delta types actually received:")
for k, v in kinds.items():
    print(f"    {k:20} x{v}")
print(f"  final blocks: {[b.type for b in final.content]}")
print()
print("  `text_stream` yields ONLY text_delta. Anything else — thinking, tool")
print("  arguments — is filtered out. Iterate the stream yourself when you need")
print("  those, and use get_final_message() to reassemble regardless.")
print()
print("  Mandatory, not optional: current models allow up to 128K max_tokens,")
print("  and a non-streaming request that large can exceed the HTTP timeout and")
print("  fail. Above roughly 16K max_tokens, stream.")

# NOTES FROM THE COURSE
# - Streaming is ONE request whose body arrives in pieces. It is not several
#   calls, and it does not change token cost.
# - ContentBlockDelta events carry the text you display.
# - `with client.messages.stream(...)` is the ergonomic path; `stream=True` on
#   create() gives raw events when you need them.
# - get_final_message() gives the assembled Message for storage, so you get
#   live output AND a normal object to append to history.
#
# DIVERGENCES / ADDITIONS, verified 31 Aug 2026
# 1. Event names on the wire are snake_case (message_start, content_block_start,
#    content_block_delta, content_block_stop, message_delta, message_stop) —
#    not the CamelCase in the lesson's list. Observed 31 Aug 2026; the API may
#    also send `ping` keepalives, which did not appear in these runs.
# 1b. Delta subtypes observed on one streamed reply: text_delta x8,
#    thinking_delta x1, signature_delta x1. The lesson mentions none of these —
#    it treats ContentBlockDelta as if it always carried text.
# 2. `text_stream` filters to text_delta only. With thinking enabled — the
#    default on current models — thinking_delta events exist and are silently
#    dropped by that helper.
# 3. Streaming becomes REQUIRED at large max_tokens to avoid HTTP timeouts.
