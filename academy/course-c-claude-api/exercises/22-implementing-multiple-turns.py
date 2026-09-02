"""
Exercise 22 — implementing multiple turns (the agentic loop).

Course C, section: "Implementing multiple turns" (Tool Use block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287758
    Code from the official 001_tools_008.ipynb.

WHAT THIS TEACHES
    Exercise 21 was hardcoded to exactly two API calls. Real code cannot
    know in advance how many tool rounds a request needs — so the flow
    becomes a LOOP with one termination test:

        while True:
            response = chat(messages, tools=[...])
            add_assistant_message(messages, response)
            if response.stop_reason != "tool_use":
                break                          # final answer reached
            add_user_message(messages, run_tools(response))

    THIS IS THE 1.1 AGENTIC LOOP. Everything the exam asks about agent
    loops is in these six lines: the model decides, the code executes, the
    loop hands results back, and stop_reason — nothing else — says when it
    is over.

    New machinery, all from the notebook:
      - helpers accept a whole Message OR plain content (isinstance check),
        so add_assistant_message(messages, response) just works
      - run_tool(name, input) — the ROUTER: name -> function. Adding a tool
        touches this router and the schema list, never the loop
      - run_tools(message) — collects ALL tool_use blocks (Claude may
        request several in one response), runs each, returns one
        tool_result block per request, ids matched
      - try/except around each call: failures become is_error=True results.
        The loop feeds errors back to the model instead of crashing — the
        model can retry or explain, and the failure stays visible (D5.3)
      - json.dumps(tool_output) — results serialised as strings; the wire
        shows content='"11:16"', quotes included

EXAM LINK
    D1.1 — the loop, verbatim. Termination is stop_reason != "tool_use";
    a text preamble in the same response means nothing (the model can say
    "let me check..." AND request a tool — printing text does not mean
    done). D1 trap from step 6: an iteration CAP is a safety fuse against
    runaway loops, not a completion condition — note the notebook's loop
    has NO cap at all; production code adds one and treats hitting it as
    an error, never as success.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/22-implementing-multiple-turns.py

    MEASURED 2 Sep 2026, claude-haiku-4-5:
        [1] stop_reason=tool_use  blocks=['tool_use', 'tool_use']  <- PARALLEL
        [1] ran tool -> "11:55" ; ran tool -> "27"
        [2] stop_reason=end_turn  blocks=['text']
        history: user(text) -> assistant([tool_use, tool_use])
                 -> user([tool_result, tool_result]) -> assistant([text])

    The notebook's recorded run answered the same question SEQUENTIALLY —
    three API calls, one tool per round. Ours batched both requests into
    one response — two API calls. Same code, both shapes: which one you
    get is the model's choice per run, which is exactly why run_tools()
    iterates over ALL tool_use blocks instead of assuming one.

    This is also step 6's re-test question answered by a live wire: after
    two parallel tool calls you append TWO messages — one assistant turn
    holding both tool_use blocks, one user turn holding both tool_results.
"""

import json
from datetime import datetime

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-haiku-4-5"              # the course uses Haiku throughout


# ------------------------------------------------- helpers, tool-use grade
# Both helpers now take EITHER a Message object (append its block list) or
# plain content (a string, or a list of blocks like tool_results). One
# signature for every kind of turn.
def add_user_message(messages, message):
    messages.append({
        "role": "user",
        "content": message.content if isinstance(message, Message) else message,
    })


def add_assistant_message(messages, message):
    messages.append({
        "role": "assistant",
        "content": message.content if isinstance(message, Message) else message,
    })


def chat(messages, system=None, stop_sequences=None, tools=None, max_tokens=1000):
    params = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    if tools:
        params["tools"] = tools
    return client.messages.create(**params)


def text_from_message(message):
    return "\n".join(b.text for b in message.content if b.type == "text")


# ------------------------------------------------------------- the tool
def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")   # feeds the is_error path
    return datetime.now().strftime(date_format)


get_current_datetime_schema = {
    "name": "get_current_datetime",
    "description": "Returns the current date and time formatted according to the specified format string. This tool provides the current system time formatted as a string. Use this tool when you need to know the current date and time, such as for timestamping records, calculating time differences, or displaying the current time to users. The default format returns the date and time in ISO-like format (YYYY-MM-DD HH:MM:SS).",
    "input_schema": {
        "type": "object",
        "properties": {
            "date_format": {
                "type": "string",
                "description": "A string specifying the format of the returned datetime. Uses Python's strftime format codes. For example, '%Y-%m-%d' returns just the date in YYYY-MM-DD format, '%H:%M:%S' returns just the time in HH:MM:SS format, '%B %d, %Y' returns a date like 'May 07, 2025'. The default is '%Y-%m-%d %H:%M:%S' which returns a complete timestamp like '2025-05-07 14:32:15'.",
                "default": "%Y-%m-%d %H:%M:%S",
            }
        },
        "required": [],
    },
}


# ----------------------------------------------------------- the router
def run_tool(tool_name, tool_input):
    """Name -> function. The ONLY place that knows which tools exist;
    the loop below never changes when tools are added."""
    if tool_name == "get_current_datetime":
        return get_current_datetime(**tool_input)


def run_tools(message):
    """Run EVERY tool_use block in the message; return one tool_result
    block per request, ids matched, failures marked — never raised."""
    tool_requests = [b for b in message.content if b.type == "tool_use"]
    tool_result_blocks = []

    for tool_request in tool_requests:
        try:
            tool_output = run_tool(tool_request.name, tool_request.input)
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": json.dumps(tool_output),    # always a string on the wire
                "is_error": False,
            }
        except Exception as e:
            # The failure goes BACK TO THE MODEL, labelled as a failure.
            # It can retry with fixed arguments or tell the user — either
            # way the error kept its error-ness crossing the boundary.
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": f"Error: {e}",
                "is_error": True,
            }

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks


# ------------------------------------------------------------- the LOOP
def run_conversation(messages):
    iteration = 0
    while True:                       # notebook has no cap — see EXAM LINK
        iteration += 1
        response = chat(messages, tools=[get_current_datetime_schema])
        print(f"[{iteration}] stop_reason={response.stop_reason}  "
              f"blocks={[b.type for b in response.content]}", flush=True)

        add_assistant_message(messages, response)   # blocks in, always
        if text := text_from_message(response):
            print(f"[{iteration}] text: {text}")

        if response.stop_reason != "tool_use":
            break                     # the ONLY exit: model stopped asking

        tool_results = run_tools(response)
        for r in tool_results:
            print(f"[{iteration}] ran tool -> {r['content']}"
                  f"{'  (ERROR)' if r['is_error'] else ''}")
        add_user_message(messages, tool_results)

    return messages


# ------------------------------------------------------------------ run
messages = []
add_user_message(
    messages,
    "What is the current time in HH:MM format? Also, what is the current time in SS format?",
)
run_conversation(messages)

print("\nfinal history shape:")
for message in messages:
    content = message["content"]
    if isinstance(content, str):
        print(f"  {message['role']}: (text) {content!r}")
    else:
        kinds = [b.type if hasattr(b, "type") else b["type"] for b in content]
        print(f"  {message['role']}: (blocks) {kinds}")

# NOTES FROM THE COURSE
# - The loop's single termination test: stop_reason != "tool_use". Printed
#   text is NOT a signal — a response can carry text AND a tool request.
# - run_tools handles MULTIPLE tool_use blocks per response; each result
#   carries the id of its request, so order does not matter.
# - Errors become is_error=True results, not exceptions: the conversation
#   survives a broken tool call and the model decides what to do next.
# - json.dumps standardises the result string ('"11:16"' on the wire).
# - The router (run_tool) is the extension point: new tool = one router
#   branch + one schema in the tools list. The loop never changes.
#
# WORTH KNOWING (Domain 1)
# - This file and exercise 04's chat bot are the SAME loop with one swap:
#   the human's input() became run_tools(). That swap is the whole
#   difference between a chat bot and an agent.
# - while True with no cap is fine in a lesson and a liability in
#   production: a model that keeps asking for tools burns budget forever.
#   The fix is a cap treated as a FAILURE when hit (step 6: a fuse, not a
#   finish line) — plus the D1.7 concern: history grows every iteration,
#   and each loop resends all of it.
# - Whether the model answers a two-part question with two sequential
#   rounds or two parallel tool_use blocks in one round is ITS choice —
#   code must handle both shapes; run_tools already does.
