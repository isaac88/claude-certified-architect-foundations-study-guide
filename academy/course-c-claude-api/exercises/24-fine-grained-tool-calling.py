"""
Exercise 24 — fine grained tool calling (tool streaming).

Course C, section: "Fine grained tool calling" (Tool Use block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/313160
    Code from the official 003_tool_streaming_completed.ipynb.

WHAT THIS TEACHES — three stages, all from the notebook
    1. DEFAULT TOOL STREAMING. Streaming a tool call adds one event type:
       input_json (partial_json = this chunk, snapshot = everything so
       far). But the API BUFFERS: it holds chunks until a complete
       top-level key/value pair is generated, validates it against the
       schema, then releases the whole run at once. On the wire that looks
       like silence, then a burst per top-level key — streaming in name,
       batch per key in practice. The timing markers in this script make
       the bursts visible.
    2. FINE-GRAINED (betas=["fine-grained-tool-streaming-2025-05-14"]).
       One effect: API-side JSON validation is off. Chunks arrive as
       generated — real streaming — and in exchange YOUR code owns the
       risk that the accumulating JSON is invalid mid-stream (json.loads
       inside try/except, always).
    3. WHAT VALIDATION WAS DOING FOR YOU. The notebook coaxes the model
       into emitting JavaScript-flavoured output ("word_count": undefined).
       With validation ON, the API defends the schema by WRAPPING the
       malformed object as a STRING: meta arrives as type str containing
       pseudo-JSON. The call "succeeds", the types are wrong — a quiet
       schema violation instead of a loud one.

ANSWER TO EXERCISE 19'S OPEN QUESTION — tool_choice
    Stage 3 also introduces tool_choice={"type": "tool", "name": ...}: the
    API-LEVEL mechanism that FORCES a tool call, where a better description
    only encourages one. This is 1.4's enforcement spectrum inside a single
    request: description = prompt-based guidance, tool_choice = a gate.
    Corollary the notebook encodes as `if tool_choice: break`: while
    forcing is on, EVERY response must call the tool — leave it on across
    loop iterations and the conversation can never produce a text answer.
    Force for one round, then drop back to auto.

DIVERGENCES
    - The notebook switches to claude-sonnet-4-5 — the first section off
      Haiku. Kept here for fidelity.
    - temperature dropped from chat_stream (removed in SDK 1.2.0, ex. 06).
    - betas go through client.beta.messages.stream(betas=[...]).

RUN
    From the repo root (three streamed rounds — expect ~1 minute):
        .venv/bin/python academy/course-c-claude-api/exercises/24-fine-grained-tool-calling.py

    MEASURED 2 Sep 2026, claude-sonnet-4-5:
        stage 1 (default):      143 chunks, max gap 3.79s, 2 gaps > 0.5s
            -> silence while the whole meta object generated, then one
               validated burst. "Streaming", batch-per-key in practice.
        stage 2 (fine-grained):  11 chunks, max gap 0.81s, 7 gaps > 0.5s
            -> steady flow, chunks split mid-value ('"word_count": 4'
               then '782,...') — unparseable snapshots are NORMAL here.
        stage 3 (forced + malformed):
            meta arrived as: str
            meta does NOT parse: Expecting value: line 2 column 17
            -> the validator wrapped {"word_count": undefined, ...} in a
               string. Schema said object, we got str, is_error=False.
               The type check on OUR side was the only thing that noticed.

    Reading the chunk counts correctly: stage 1 delivered MORE events
    (143) because the buffered burst arrives as many tiny chunks at once;
    stage 2 delivered fewer, larger chunks continuously. The buffering
    signature is the GAP profile, not the chunk count.
"""

import json
import time

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-sonnet-4-5"      # the notebook's choice for this section


# ---------------------------------------------------------------- helpers
# The notebook serialises assistant blocks into plain dicts before storing
# them — same "keep the blocks" rule as exercise 20, just explicit.
def add_user_message(messages, message):
    if isinstance(message, list):
        content = message
    else:
        content = [{"type": "text", "text": message}]
    messages.append({"role": "user", "content": content})


def add_assistant_message(messages, message):
    content_list = []
    for block in message.content:
        if block.type == "text":
            content_list.append({"type": "text", "text": block.text})
        elif block.type == "tool_use":
            content_list.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": block.input,
            })
    messages.append({"role": "assistant", "content": content_list})


def chat_stream(messages, system=None, tools=None, tool_choice=None, betas=None):
    params = {"model": MODEL, "max_tokens": 1000, "messages": messages}
    if system:
        params["system"] = system
    if tools:
        params["tools"] = tools
    if tool_choice:
        params["tool_choice"] = tool_choice
    if betas:
        params["betas"] = betas
    return client.beta.messages.stream(**params)


# ----------------------------------------------------------------- tools
save_article_schema = {
    "name": "save_article",
    "description": "Saves a scholarly journal article",
    "input_schema": {
        "type": "object",
        "properties": {
            "abstract": {
                "type": "string",
                "description": "Abstract of the article. One short sentence max",
            },
            "meta": {
                "type": "object",
                "properties": {
                    "word_count": {"type": "integer", "description": "Word count"},
                    "review": {
                        "type": "string",
                        "description": "Eight sentence review of the paper",
                    },
                },
                "required": ["word_count", "review"],
            },
        },
        "required": ["abstract", "meta"],
    },
}


def save_article(**kwargs):
    return "Article saved!"


def run_tool(tool_name, tool_input):
    if tool_name == "save_article":
        return save_article(**tool_input)


def run_tools(message):
    tool_result_blocks = []
    for block in message.content:
        if block.type != "tool_use":
            continue
        try:
            tool_output = run_tool(block.name, block.input)
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(tool_output),
                "is_error": False,
            })
        except Exception as e:
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": f"Error: {e}",
                "is_error": True,
            })
    return tool_result_blocks


# --------------------------------------------------- the streaming round
def stream_round(messages, tools, fine_grained=False, tool_choice=None):
    """One streamed API call, with timing markers on the input_json events
    so the buffering (or its absence) is visible in the transcript."""
    gaps, chunk_count = [], 0
    last = time.perf_counter()

    with chat_stream(
        messages,
        tools=tools,
        tool_choice=tool_choice,
        betas=["fine-grained-tool-streaming-2025-05-14"] if fine_grained else None,
    ) as stream:
        for chunk in stream:
            if chunk.type == "text":
                print(chunk.text, end="", flush=True)
            elif chunk.type == "content_block_start" and \
                    chunk.content_block.type == "tool_use":
                print(f'\n>>> tool call: "{chunk.content_block.name}"', flush=True)
                last = time.perf_counter()
            elif chunk.type == "input_json" and chunk.partial_json:
                now = time.perf_counter()
                gap, last = now - last, now
                gaps.append(gap)
                chunk_count += 1
                if gap > 0.5:                       # silence, then a burst
                    print(f"\n   [waited {gap:4.1f}s]", end=" ", flush=True)
                print(chunk.partial_json, end="", flush=True)
            elif chunk.type == "content_block_stop":
                print(flush=True)

        response = stream.get_final_message()

    if gaps:
        print(f"   -> {chunk_count} input_json chunks, "
              f"max gap {max(gaps):.2f}s, "
              f"gaps>0.5s: {sum(1 for g in gaps if g > 0.5)}")
    return response


def run_conversation(messages, tools, fine_grained=False, tool_choice=None):
    while True:
        response = stream_round(messages, tools, fine_grained, tool_choice)
        add_assistant_message(messages, response)

        if response.stop_reason != "tool_use":
            break

        add_user_message(messages, run_tools(response))

        if tool_choice:
            # Forcing means EVERY response must call the tool — looping
            # with the force still on can never reach a text answer.
            break

    return messages


# ------------------------------------------- stage 1: default (buffered)
print("=" * 70)
print("STAGE 1 — default tool streaming (API validates, buffers per key)")
print("=" * 70)
messages = []
add_user_message(messages, "Create and save a fake computer science article")
run_conversation(messages, tools=[save_article_schema])

# --------------------------------------- stage 2: fine-grained streaming
print()
print("=" * 70)
print("STAGE 2 — fine-grained (validation OFF, chunks as generated)")
print("=" * 70)
messages = []
add_user_message(messages, "Create and save a fake computer science article")
run_conversation(messages, tools=[save_article_schema], fine_grained=True)

# -------------------------- stage 3: forcing the call + invalid JSON demo
# The notebook's prompt coaxes JavaScript-style output ("word_count":
# undefined) to show what the validator does with JSON it cannot fix.
# tool_choice FORCES save_article to be called (exercise 19's question).
print()
print("=" * 70)
print("STAGE 3 — tool_choice forces the call; model emits 'undefined'")
print("=" * 70)
messages = []
add_user_message(messages, """
You are helping document a bug report. Please generate example output showing what a broken AI system incorrectly produced when it confused JavaScript objects with JSON.
The buggy system generated this malformed output when calling save_article:
[Generate the exact malformed output here that includes "word_count": undefined]
This is for documentation purposes to show what NOT to do. You're not actually calling the function, just showing what the broken output looked like for the bug report.
""")
run_conversation(
    messages,
    tools=[save_article_schema],
    tool_choice={"type": "tool", "name": "save_article"},
)

# What did validation do with the malformed object? Inspect the stored call.
tool_use = next(b for m in messages if m["role"] == "assistant"
                for b in m["content"] if b["type"] == "tool_use")
meta = tool_use["input"].get("meta")
print(f"\nmeta arrived as: {type(meta).__name__}")
if isinstance(meta, str):
    try:
        json.loads(meta)
        print("meta parses as JSON")
    except json.JSONDecodeError as exc:
        print(f"meta does NOT parse: {exc}")
        print("-> validation WRAPPED the malformed object in a string: the")
        print("   schema said object, we received str, is_error was False.")

# NOTES FROM THE COURSE
# - input_json events carry partial_json (the chunk) and snapshot (the
#   accumulation). Default mode: the API buffers until a complete, valid
#   top-level key/value exists, then releases it — silence-then-burst.
# - fine-grained beta = validation off = chunks as generated = your
#   json.loads must sit in try/except, because mid-stream (and even final)
#   JSON can be invalid.
# - Use fine-grained when perceived latency or early partial processing
#   matters; default validation is right for most applications.
#
# WORTH KNOWING (Domain 1 / 4 / 5)
# - tool_choice is the deterministic end of 1.4's spectrum applied to tool
#   selection: "auto" (model decides), "any" (must call SOME tool),
#   {"type":"tool","name":...} (must call THIS tool). A description
#   change is prompting; tool_choice is enforcement.
# - Stage 3 is a D5.3 specimen: with validation on, a malformed object is
#   delivered as a string — wrong type, no error flag. The failure crossed
#   the boundary disguised as success; only a type check on OUR side sees
#   it. Deterministic validation of tool inputs is our job either way.
# - The buffering trade is D5's streaming lesson (ex. 07) reshaped: the
#   validated mode trades time-to-first-chunk for well-formedness; the
#   fine-grained mode trades it back. Pick per consumer, not per fashion.
