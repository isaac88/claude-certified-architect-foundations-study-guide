"""
Exercise 19 — tool functions and tool schemas.

Course C, sections: "Introducing tool use" / "Tool functions" / "Tool
schemas" (start of the Tool Use block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    (paste the section URL here)
    Code from the official 001_tools.ipynb.

WHAT THIS TEACHES
    A "tool" is two things, and only one of them is code:
      1. the FUNCTION — ordinary Python, lives on OUR side, Claude never
         sees it and never executes it
      2. the SCHEMA — a JSON description of the function (name, what it
         does, what arguments it takes) that we SEND with the request
    Claude reads schemas, not code. When it decides a tool would help, it
    does not call anything — it REPLIES with a tool_use content block: a
    structured request saying "please run <name> with <input> and tell me
    what came back". Execution, and the decision to execute, stay with us.

    This exercise stops at exactly that moment: define the function, write
    the schema, send a question the model cannot answer alone, and inspect
    the tool_use block in the reply. ANSWERING the request (tool_result) is
    the next section.

WHY THE DESCRIPTION IS SO LONG
    The schema's description is the tool's entire interface as far as
    Claude is concerned — it picks tools, fills arguments and interprets
    results from that text alone. A vague description produces wrong or
    missing tool calls the same way a vague prompt produces wrong output.
    Same discipline as exercise 16, pointed at a different consumer:
    the description is prompt engineering for the model's tool choice.

EXAM LINK
    D1.1 — this is the response shape the exam drills: stop_reason is
    "tool_use", content is a LIST whose last block is tool_use (id, name,
    input). Two classic traps live here:
      - content[0].text raises or misleads when a tool_use block is present
        (there may be NO text block at all — verified in exercise 02)
      - stop_reason="tool_use" is NOT a finished answer; treating it as one
        is the premature-stop bug from step 6
    D2 — schema quality (names, descriptions, required vs defaulted
    parameters) is tool DESIGN, domain 2's subject.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/19-tool-functions-and-schemas.py

    MEASURED 2 Sep 2026, claude-haiku-4-5:
        stop_reason: tool_use
        blocks:      ['tool_use']        <- NO text block AT ALL
        input:       {'datetime_str': '2026-03-15', 'duration': 90,
                      'unit': 'days'}    (defaults omitted, as the schema allows)

    Note what the model did with the prompt: "March 15, 2026" arrived in
    prose and left as ISO "2026-03-15" matching the schema's default
    input_format — argument-filling is a translation step, driven entirely
    by the schema text. And the block list is the exam trap in the flesh:
    no text block, so the notebook's own chat() (return content[0].text)
    would raise AttributeError on this exact response.
"""

from datetime import datetime, timedelta

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-haiku-4-5"              # the course uses Haiku throughout


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def chat(messages, system=None, stop_sequences=None, tools=None, max_tokens=1000):
    """The block's chat() with one addition: `tools` — a list of SCHEMAS
    (not functions!) passed straight through to the API. Sending a schema
    is what makes the tool exist from Claude's point of view."""
    params = {"model": MODEL, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    if tools:
        params["tools"] = tools
    return client.messages.create(**params)


# ---------------------------------------------------- 1. the tool FUNCTION
# Ordinary Python. Nothing about it is special: no decorator, no SDK
# import, no registration. Claude never sees this code.
def add_duration_to_datetime(datetime_str, duration=0, unit="days",
                             input_format="%Y-%m-%d"):
    # Parse the incoming string into a datetime using the caller-supplied
    # format (defaults to ISO dates like "2026-09-02").
    date = datetime.strptime(datetime_str, input_format)

    # timedelta handles the fixed-length units directly.
    if unit == "seconds":
        new_date = date + timedelta(seconds=duration)
    elif unit == "minutes":
        new_date = date + timedelta(minutes=duration)
    elif unit == "hours":
        new_date = date + timedelta(hours=duration)
    elif unit == "days":
        new_date = date + timedelta(days=duration)
    elif unit == "weeks":
        new_date = date + timedelta(weeks=duration)
    elif unit == "months":
        # Months are NOT fixed-length, so timedelta cannot do this. Add to
        # the month number, carry into the year, then clamp the day to the
        # target month's length (Jan 31 + 1 month must be Feb 28/29).
        month = date.month + duration
        year = date.year + month // 12
        month = month % 12
        if month == 0:
            month = 12
            year -= 1
        day = min(
            date.day,
            [31,
             29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
             31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1],
        )
        new_date = date.replace(year=year, month=month, day=day)
    elif unit == "years":
        new_date = date.replace(year=date.year + duration)
    else:
        raise ValueError(f"Unsupported time unit: {unit}")

    # Return a rich human-readable string — this exact wording is promised
    # in the schema's description below, and Claude will repeat it to the
    # user, so function and schema must tell the same story.
    return new_date.strftime("%A, %B %d, %Y %I:%M:%S %p")


# ------------------------------------------------------ 2. the tool SCHEMA
# This dict is what Claude actually receives. Three parts:
#   name          how the tool_use block will refer to the function
#   description   the ENTIRE interface from Claude's side — when to use it,
#                 what it handles (months! leap years!), what comes back
#   input_schema  JSON Schema for the arguments: types, per-argument
#                 descriptions, and which are required. datetime_str is the
#                 only required one; the rest declare their defaults IN THE
#                 DESCRIPTION so Claude knows omitting them is safe.
add_duration_to_datetime_schema = {
    "name": "add_duration_to_datetime",
    "description": "Adds a specified duration to a datetime string and returns the resulting datetime in a detailed format. This tool converts an input datetime string to a Python datetime object, adds the specified duration in the requested unit, and returns a formatted string of the resulting datetime. It handles various time units including seconds, minutes, hours, days, weeks, months, and years, with special handling for month and year calculations to account for varying month lengths and leap years. The output is always returned in a detailed format that includes the day of the week, month name, day, year, and time with AM/PM indicator (e.g., 'Thursday, April 03, 2025 10:30:00 AM').",
    "input_schema": {
        "type": "object",
        "properties": {
            "datetime_str": {
                "type": "string",
                "description": "The input datetime string to which the duration will be added. This should be formatted according to the input_format parameter.",
            },
            "duration": {
                "type": "number",
                "description": "The amount of time to add to the datetime. Can be positive (for future dates) or negative (for past dates). Defaults to 0.",
            },
            "unit": {
                "type": "string",
                "description": "The unit of time for the duration. Must be one of: 'seconds', 'minutes', 'hours', 'days', 'weeks', 'months', or 'years'. Defaults to 'days'.",
            },
            "input_format": {
                "type": "string",
                "description": "The format string for parsing the input datetime_str, using Python's strptime format codes. For example, '%Y-%m-%d' for ISO format dates like '2025-04-03'. Defaults to '%Y-%m-%d'.",
            },
        },
        "required": ["datetime_str"],
    },
}


# ------------------------------------------- 3. send the schema to Claude
# A question the model should not trust itself on: calendar arithmetic
# across month boundaries. With the schema attached, the correct behaviour
# is to ASK US to run the tool rather than guess.
messages = []
add_user_message(messages, "What date is 90 days after March 15, 2026?")

response = chat(messages, tools=[add_duration_to_datetime_schema])

# ---------------------------------------------------- 4. inspect the reply
print(f"stop_reason: {response.stop_reason}")
print(f"blocks:      {[block.type for block in response.content]}\n")

for block in response.content:
    if block.type == "text":
        print(f"text block:\n  {block.text}\n")
    elif block.type == "tool_use":
        print("tool_use block — Claude is ASKING, not executing:")
        print(f"  id:    {block.id}          (we must echo this back with the result)")
        print(f"  name:  {block.name}")
        print(f"  input: {block.input}")

print("\nNOT answered yet: stop_reason='tool_use' means the turn is a request")
print("for execution, not a completed answer. Running the function and sending")
print("a tool_result back is the next section (exercise 20).")

# NOTES FROM THE COURSE
# - Tool = function (ours, private) + schema (sent with every request).
# - Claude never executes anything. It emits a tool_use block: id, name,
#   input. The id is the correlation key for the result we send back.
# - Long descriptions are deliberate: Claude chooses and parameterises
#   tools ONLY from the schema text. Say when to use it, what edge cases
#   it handles, and exactly what it returns.
# - input_schema is standard JSON Schema: property types + descriptions +
#   a required list. Optional parameters state their defaults in prose.
#
# WORTH KNOWING (Domain 1 / Domain 2)
# - The input Claude produces is MODEL OUTPUT, not validated data: nothing
#   guarantees unit is one of the seven strings the description lists (the
#   schema does not use an enum — it could, and D2 says it should; the
#   function's ValueError is the backstop when prose is ignored).
# - The function was designed FOR a model caller: strings in, a single
#   self-describing string out. A version returning a datetime object
#   would be useless — tool results travel back as text.
# - stop_reason="tool_use" + a content LIST is the exam's favourite
#   response shape. content[0] is not guaranteed to be text, and nothing
#   here is a final answer.
