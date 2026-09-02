"""
Exercise 21 — sending tool results.

Course C, section: "Sending tool results" (Tool Use block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287752

WHAT THIS TEACHES
    Steps 3-5 of the flow exercise 20 left hanging: run the function Claude
    asked for, send the result back, receive the real answer.

    The result travels in a tool_result block INSIDE A USER MESSAGE — from
    the API's point of view, we are just another party reporting facts:
        {"type": "tool_result",
         "tool_use_id": <the tool_use block's id>,   # correlation key
         "content": <function output AS A STRING>,
         "is_error": False}                          # True if the call blew up

    Three rules the lesson stresses:
      - tool_use_id must match the requesting block's id — that is how
        results pair with requests when several tools run at once
      - the follow-up request needs the FULL history (stateless API)
      - the follow-up must still send tools=[...]: Claude needs the schema
        to interpret the tool blocks already sitting in that history

DIVERGENCE — the lesson indexes, the current model punishes it
    The lesson reads the request as response.content[1].input: index 1,
    because it assumes block 0 is the polite text preamble. Exercises 19
    and 20 measured blocks == ['tool_use'] on claude-haiku-4-5 — no
    preamble, so content[1] raises IndexError on the current model. Same
    fragile-indexing disease as content[0].text (exercise 02). This file
    finds the block by TYPE:
        next(b for b in response.content if b.type == "tool_use")

EXAM LINK
    D1.1 — the complete loop shape the exam expects you to narrate:
    user -> assistant(tool_use) -> user(tool_result) -> assistant(text).
    Watch the stop_reasons flip: tool_use on the request turn, end_turn on
    the answer turn — THAT is the completion signal, nothing else.
    D5.3 — is_error exists so a failed tool call goes back marked as a
    failure instead of vanishing or masquerading as data.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/21-sending-tool-results.py

    MEASURED 2 Sep 2026, claude-haiku-4-5:
        turn 1: stop_reason=tool_use  blocks=['tool_use']
        ran     get_current_datetime(**{'date_format': '%H:%M:%S'}) -> '11:01:11'
        turn 2: stop_reason=end_turn  blocks=['text']
        answer: "The exact time is **11:01:11** (HH:MM:SS format)."

    Conversation shape, verbatim from the run — memorise this for the exam:
        user(text) -> assistant([tool_use]) -> user([tool_result])
        -> assistant([text])
    And note the lesson's own content[1] would have raised IndexError on
    turn 1: blocks was ['tool_use'], nothing at index 1.
"""

from datetime import datetime

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-haiku-4-5"              # the course uses Haiku throughout


def add_user_message(messages, content):
    messages.append({"role": "user", "content": content})


def add_assistant_message(messages, content):
    messages.append({"role": "assistant", "content": content})


def chat(messages, system=None, stop_sequences=None, tools=None, max_tokens=1000):
    params = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    if tools:
        params["tools"] = tools
    return client.messages.create(**params)


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


# ----------------------------------------------- the tool (exercise 20's)
def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    return datetime.now().strftime(date_format)


get_current_datetime_schema = {
    "name": "get_current_datetime",
    "description": "Returns the current date and time, formatted according to the provided format string. Use this whenever the user asks about the current date, the current time, or anything that requires knowing what time it is right now. The format string uses Python strftime codes (e.g. '%Y-%m-%d' for an ISO date, '%H:%M:%S' for a 24-hour time). If no format is provided, the full date and time is returned as 'YYYY-MM-DD HH:MM:SS'.",
    "input_schema": {
        "type": "object",
        "properties": {
            "date_format": {
                "type": "string",
                "description": "Python strftime format string for the returned value. For example '%H:%M:%S' to get only the time. Defaults to '%Y-%m-%d %H:%M:%S'.",
            },
        },
        "required": [],
    },
}


# --------------------------------------------- steps 1-2 (as exercise 20)
messages = []
add_user_message(messages, "What is the exact time, formatted as HH:MM:SS?")

response = chat(messages, tools=[get_current_datetime_schema])
print(f"turn 1  stop_reason={response.stop_reason}  "
      f"blocks={[b.type for b in response.content]}")

# History gets the block list, unanswered tool_use and all (exercise 20).
add_assistant_message(messages, response.content)

# --------------------------------------------------- step 3: run the tool
# Find the request by TYPE, not position — see DIVERGENCE in the header.
tool_use = next(b for b in response.content if b.type == "tool_use")

# block.input is a dict; the function wants keyword arguments -> unpack.
tool_output = get_current_datetime(**tool_use.input)
print(f"executed {tool_use.name}(**{tool_use.input}) -> {tool_output!r}")

# ------------------------------------------- step 4: send the result back
# A USER message whose content is a tool_result block. The id pairs this
# result with the request; content must be a string; is_error=False says
# the call succeeded (on an exception we would send the error text with
# is_error=True instead — never silently drop a failure, D5.3).
add_user_message(messages, [
    {
        "type": "tool_result",
        "tool_use_id": tool_use.id,
        "content": str(tool_output),
        "is_error": False,
    }
])

# --------------------------------------------- step 5: the final response
# tools= is STILL passed: the history contains tool blocks, and Claude
# needs the schema to make sense of them.
final = chat(messages, tools=[get_current_datetime_schema])
print(f"turn 2  stop_reason={final.stop_reason}  "
      f"blocks={[b.type for b in final.content]}")

print(f"\nfinal answer: {text_of(final)}")

print("\nfull conversation shape:")
for message in messages + [{"role": "assistant", "content": final.content}]:
    content = message["content"]
    if isinstance(content, str):
        print(f"  {message['role']}: (text) {content!r}")
    else:
        kinds = [b.type if hasattr(b, "type") else b["type"] for b in content]
        print(f"  {message['role']}: (blocks) {kinds}")

# NOTES FROM THE COURSE
# - Unpack block.input with ** — Claude sends a dict, functions take kwargs.
# - tool_result lives in a USER message: tool_use_id + content (string) +
#   is_error. The id matching is what keeps multiple simultaneous tool
#   calls unambiguous even if results are sent back in a different order.
# - Resend the FULL history plus the result, and keep tools=[...] in the
#   follow-up — the schema is needed to interpret history, not just to
#   enable new calls.
# - Claude can emit SEVERAL tool_use blocks in one response ("what's 10+10
#   and 30+30?") — each gets its own id and its own tool_result. That is
#   the coming sections' material.
#
# WORTH KNOWING (Domain 1)
# - The stop_reason flip is the whole loop-control story: tool_use said
#   "not done, run this"; end_turn says "done". The step-6 exam answer in
#   one run of one script.
# - Nothing stops Claude from responding to a tool_result with ANOTHER
#   tool_use — which is why real code wraps this in a while loop on
#   stop_reason, not a fixed two-call script. That loop is "multi-turn
#   conversations with tools", up next.
