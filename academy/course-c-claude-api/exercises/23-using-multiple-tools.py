"""
Exercise 23 — using multiple tools.

Course C, section: "Using multiple tools" (Tool Use block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287749
    Code from the official 001_tools_009.ipynb.

WHAT THIS TEACHES
    Exercise 22's infrastructure was built so that THIS lesson is trivial.
    Adding a tool is four steps, none of which touch the loop:
      1. write the function
      2. write the schema
      3. append the schema to the tools list
      4. add an elif to the run_tool router
    Three tools now serve a reminder assistant: get_current_datetime,
    add_duration_to_datetime (exercise 19's — models are bad at calendar
    maths), and set_reminder.

    The test request FORCES CHAINING: "Set a reminder for my doctors
    appointment. Its 177 days after Jan 1st, 2050." The reminder cannot be
    set until the date is computed — the second tool's input IS the first
    tool's output. Unlike exercise 22's two independent questions (which
    the model batched in parallel), a data dependency forces sequential
    rounds. The MODEL discovered that ordering from the schemas alone;
    nobody told it a plan.

TOOL-DESIGN WART, straight from the notebook's own transcript
    set_reminder returns None, so its tool_result content is the string
    'null' with is_error=False — and the model REPLIED "Your reminder has
    been set successfully!". It inferred success from a null. It would
    have said the same if the reminder silently failed. A tool should
    return an explicit confirmation ("reminder stored for <ts>") so the
    model reports facts rather than optimism. D2 lesson free of charge —
    and D5.3 again: absence of an error is not evidence of success.

EXAM LINK
    D1.6 (task decomposition) — dependent steps sequential, independent
    steps parallel, chosen by the model per request; exercises 22 and 23
    are the two shapes side by side. D2 — the router + schema list is the
    entire integration surface for new tools.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/23-using-multiple-tools.py

    MEASURED 2 Sep 2026, claude-haiku-4-5 — three iterations, all shapes:
        [1] tool_use   ['tool_use']            add_duration -> "Monday, June 27, 2050..."
        [2] tool_use   ['text', 'tool_use']    set_reminder -> 'null'
        [3] end_turn   ['text']                "Perfect! I've set a reminder..."

    Three findings in one run:
      - the DEPENDENCY forced sequential rounds (3 API calls), where
        exercise 22's independent questions were batched in parallel (2) —
        same code, the model chose the ordering both times
      - iteration 2 is the multi-block pairing the lessons kept promising:
        explanatory text AND a tool_use in one assistant message
      - the wart, live: set_reminder returned 'null' and the model told
        the user "Perfect! I've set a reminder... You'll receive a
        notification" — none of which it can know from a null.
"""

import json
from datetime import datetime, timedelta

from anthropic import Anthropic
from anthropic.types import Message
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-haiku-4-5"              # the course uses Haiku throughout


# --------------------------------------------- helpers (as exercise 22)
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


# ------------------------------------------------------- the three tools
def get_current_datetime(date_format="%Y-%m-%d %H:%M:%S"):
    if not date_format:
        raise ValueError("date_format cannot be empty")
    return datetime.now().strftime(date_format)


def add_duration_to_datetime(datetime_str, duration=0, unit="days",
                             input_format="%Y-%m-%d"):
    """Exercise 19's calendar arithmetic, unchanged."""
    date = datetime.strptime(datetime_str, input_format)

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

    return new_date.strftime("%A, %B %d, %Y %I:%M:%S %p")


def set_reminder(content, timestamp):
    # Stand-in for a real scheduler. NOTE: returns None — see the WART in
    # the header. json.dumps(None) -> 'null' is what Claude receives.
    print(f"----\nSetting the following reminder for {timestamp}:\n{content}\n----")


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

set_reminder_schema = {
    "name": "set_reminder",
    "description": "Creates a timed reminder that will notify the user at the specified time with the provided content. This tool schedules a notification to be delivered to the user at the exact timestamp provided. It should be used when a user wants to be reminded about something specific at a future point in time. The reminder system will store the content and timestamp, then trigger a notification through the user's preferred notification channels (mobile alerts, email, etc.) when the specified time arrives. Reminders are persisted even if the application is closed or the device is restarted. Users can rely on this function for important time-sensitive notifications such as meetings, tasks, medication schedules, or any other time-bound activities.",
    "input_schema": {
        "type": "object",
        "properties": {
            "content": {
                "type": "string",
                "description": "The message text that will be displayed in the reminder notification. This should contain the specific information the user wants to be reminded about, such as 'Take medication', 'Join video call with team', or 'Pay utility bills'.",
            },
            "timestamp": {
                "type": "string",
                "description": "The exact date and time when the reminder should be triggered, formatted as an ISO 8601 timestamp (YYYY-MM-DDTHH:MM:SS) or a Unix timestamp. The system handles all timezone processing internally, ensuring reminders are triggered at the correct time regardless of where the user is located. Users can simply specify the desired time without worrying about timezone configurations.",
            },
        },
        "required": ["content", "timestamp"],
    },
}

TOOLS = [
    get_current_datetime_schema,
    add_duration_to_datetime_schema,
    set_reminder_schema,
]


# ------------------------------------------- the router, three tools now
def run_tool(tool_name, tool_input):
    if tool_name == "get_current_datetime":
        return get_current_datetime(**tool_input)
    elif tool_name == "add_duration_to_datetime":
        return add_duration_to_datetime(**tool_input)
    elif tool_name == "set_reminder":
        return set_reminder(**tool_input)


def run_tools(message):
    tool_requests = [b for b in message.content if b.type == "tool_use"]
    tool_result_blocks = []

    for tool_request in tool_requests:
        try:
            tool_output = run_tool(tool_request.name, tool_request.input)
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": json.dumps(tool_output),
                "is_error": False,
            }
        except Exception as e:
            tool_result_block = {
                "type": "tool_result",
                "tool_use_id": tool_request.id,
                "content": f"Error: {e}",
                "is_error": True,
            }

        tool_result_blocks.append(tool_result_block)

    return tool_result_blocks


# --------------------------------------- the loop, UNCHANGED from ex. 22
def run_conversation(messages):
    iteration = 0
    while True:
        iteration += 1
        response = chat(messages, tools=TOOLS)
        print(f"[{iteration}] stop_reason={response.stop_reason}  "
              f"blocks={[b.type for b in response.content]}", flush=True)

        add_assistant_message(messages, response)
        if text := text_from_message(response):
            print(f"[{iteration}] text: {text}")

        if response.stop_reason != "tool_use":
            break

        tool_results = run_tools(response)
        for r in tool_results:
            print(f"[{iteration}] {r['content']!r:.60}"
                  f"{'  (ERROR)' if r['is_error'] else ''}")
        add_user_message(messages, tool_results)

    return messages


# ------------------------------------------------------------------ run
messages = []
add_user_message(
    messages,
    "Set a reminder for my doctors appointment. Its 177 days after Jan 1st, 2050.",
)
run_conversation(messages)

print("\nfinal history shape:")
for message in messages:
    content = message["content"]
    if isinstance(content, str):
        print(f"  {message['role']}: (text) {content!r}")
    else:
        kinds = [b.type if hasattr(b, "type") else b["type"] for b in content]
        names = [b.name for b in content if hasattr(b, "type") and b.type == "tool_use"]
        suffix = f"  {names}" if names else ""
        print(f"  {message['role']}: (blocks) {kinds}{suffix}")

# NOTES FROM THE COURSE
# - New tool = function + schema + tools-list entry + router elif. The
#   loop, run_tools and the history handling never change.
# - The reminder request chains tools: compute the date, then set the
#   reminder with the computed value. Claude sequences that itself.
# - The transcript shows multi-block assistant turns: explanatory text AND
#   a tool_use in the same message.
#
# WORTH KNOWING (Domain 1 / Domain 2)
# - Exercises 22 vs 23 are the decomposition pair (D1.6): independent
#   subtasks -> the model batches tool calls in parallel; data-dependent
#   subtasks -> it must go sequentially, because the second input needs
#   the first output. The model derives the dependency graph from the
#   schemas and the request — the code is identical in both files.
# - set_reminder's 'null' result is a D2 anti-pattern preserved for study:
#   the model declared success it could not verify. Tools should return
#   explicit confirmations; "no error" is not "worked" (D5.3).
# - The if/elif router scales linearly and is fine at 3 tools; a dict of
#   name -> function is the obvious refactor at 10 (same idea as
#   grade_syntax's dispatch in exercise 13).
