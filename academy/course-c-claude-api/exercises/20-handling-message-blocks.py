"""
Exercise 20 — handling message blocks.

Course C, section: "Handling message blocks" (Tool Use block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287757

WHAT THIS TEACHES
    Two things change the moment tools enter the conversation:

    1. RESPONSES BECOME MULTI-BLOCK. A tool-using reply typically carries
       a text block ("Let me look that up for you") AND a tool_use block
       (id, name, input). Sometimes — exercise 19 measured it — the text
       block is absent entirely. Code must iterate content, never index it.

    2. HISTORY MUST PRESERVE BLOCKS. The API is stateless (exercise 03):
       we append Claude's reply to `messages` ourselves. With tools, the
       thing appended must be the BLOCK LIST itself:
           messages.append({"role": "assistant", "content": response.content})
       Flattening to a string keeps the words and destroys the tool_use
       block — and with it the id that the next turn's tool_result must
       reference. add_assistant_message() is upgraded to accept both plain
       text and block lists.

    The five-step flow this belongs to (steps 1-2 happen here, 3-5 are the
    next section):
      1. send user message + tool schemas
      2. receive assistant message: text block + tool_use block
      3. run the real function with the tool_use input
      4. send the result back WITH the full history
      5. receive the final text answer

THIS REPO GOT HERE EARLY
    The divergence table has said "append response.content, not a string"
    since exercise 03, and reference/history-replay-with-tools.py proved
    the failure live: a string history makes the NEXT call 400 ("Each
    'tool_result' block must have a corresponding 'tool_use' block in the
    previous message"). This lesson is where the course catches up with
    its own earlier helper.

EXAM LINK
    D1.1 + D1.7 — the assistant history entry is STRUCTURED STATE, not
    prose. The exam's broken-replay stem hides exactly here: everything
    "works" until the turn after the flattening, and the error surfaces
    one message later than the bug. Trace failure to origin.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/20-handling-message-blocks.py

    MEASURED 2 Sep 2026, claude-haiku-4-5:
        stop_reason: tool_use
        blocks:      ['tool_use']
        input:       {'date_format': '%H:%M:%S'}   <- prose "HH:MM:SS"
                     translated to strftime codes by the schema text alone

    DIVERGENCE, live: the lesson says a tool reply "typically contains" a
    text block plus a tool_use block. On claude-haiku-4-5, both this run
    and exercise 19's produced tool_use ONLY — no polite preamble. The
    "typical" pairing is model-dependent behaviour, not an API guarantee,
    which is precisely why the code iterates blocks instead of assuming
    any layout.
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
    """Upgraded for tools: `content` may be plain text OR a block list
    (response.content). Both are legal values for the API's content field;
    only the block list keeps tool_use intact."""
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


# ------------------------------------------------- the lesson's new tool
# A tool the model CANNOT fake: it has no clock. Exercise 19's date maths
# was checkable; the current time is strictly unknowable to the model.
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


# -------------------------------------- steps 1-2 of the five-step flow
messages = []
add_user_message(messages, "What is the exact time, formatted as HH:MM:SS?")

response = chat(messages, tools=[get_current_datetime_schema])

print(f"stop_reason: {response.stop_reason}")
print(f"blocks:      {[block.type for block in response.content]}\n")

# Iterate — never index. The text block may or may not be there.
for block in response.content:
    if block.type == "text":
        print(f"text block:     {block.text!r}")
    elif block.type == "tool_use":
        print(f"tool_use block: id={block.id}")
        print(f"                name={block.name}, input={block.input}")

# --------------------------------- append the reply to history PROPERLY
# The block list goes in whole. This is the line the whole lesson exists
# for — response.content, not text_of(response).
add_assistant_message(messages, response.content)

print("\nhistory now holds:")
for message in messages:
    content = message["content"]
    if isinstance(content, str):
        print(f"  {message['role']}: (text) {content!r}")
    else:
        print(f"  {message['role']}: (blocks) {[b.type for b in content]}")

print("\nStopped mid-flow ON PURPOSE: history ends with an unanswered tool_use.")
print("Running the function and sending the tool_result is the next section.")

# NOTES FROM THE COURSE
# - tools=[...] in the request is what makes multi-block replies possible;
#   the reply then typically pairs a human-readable text block with the
#   machine-readable tool_use block.
# - The tool_use block: id (correlation key), name, input dict, type.
# - History with tools: append {"role": "assistant", "content":
#   response.content}. The helpers must accept block lists, not just text.
# - Five-step flow; this lesson covers receiving and storing the request.
#
# WORTH KNOWING (Domain 1)
# - WHY the block list matters: the next user turn will carry a
#   tool_result referencing the tool_use id. The API validates that pairing
#   against the PREVIOUS assistant message — flatten it to a string and the
#   next call 400s. Verified live in reference/history-replay-with-tools.py.
# - The failure is displaced in time: the flattening turn succeeds, the
#   following turn errors. Exam habit: trace the failure to its origin, one
#   message earlier than the stack trace.
# - text_of() still has a job — DISPLAYING text to a user. The lesson's
#   point is narrower than "never extract text": extraction is for display,
#   never for storage.
