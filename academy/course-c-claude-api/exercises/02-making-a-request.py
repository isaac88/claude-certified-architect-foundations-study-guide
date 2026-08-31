"""
Exercise 02 — the create() function, messages, and extracting the response.

Course C, section: "Making a request".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287725

WHAT THIS TEACHES
    The three required parameters of client.messages.create():
      model       — which Claude to call
      max_tokens  — a SAFETY LIMIT, not a target. Claude writes what it
                    thinks appropriate and is cut off if it exceeds this.
      messages    — the conversation so far, as a list of {role, content}
                    dicts. role is "user" (written by a human) or
                    "assistant" (written by Claude).

    Then: how to get the text out — and why the course's way is unsafe.

EXAM LINK (Domain 1, task 1.1)
    The course teaches `message.content[0].text`. That is the anti-pattern
    the exam tests. This file runs it next to the correct version so you
    can see which one survives.

RUN
    From the repo root (single venv, the one your IDE selects):
        .venv/bin/python academy/course-c-claude-api/exercises/02-making-a-request.py
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

# The course sets model = "claude-sonnet-4-0". That ID is no longer in the
# models list (checked 31 Aug 2026 via client.models.list()). Use a current one.
MODEL = "claude-opus-5"

message = client.messages.create(
    model=MODEL,
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": "What is quantum computing? Answer in one sentence",
        }
    ],
)

print("model:      ", message.model)
print("stop_reason:", message.stop_reason)
print("blocks:     ", [b.type for b in message.content])
print("usage:      ", message.usage.input_tokens, "in /", message.usage.output_tokens, "out")
print()

# ---------------------------------------------------------------- the course's way
print("--- the course's extraction: message.content[0].text ---")
try:
    print(message.content[0].text)
except AttributeError as exc:
    print(f"AttributeError: {exc}")
    print("The first block is not a text block, so it has no .text attribute.")
print()

# ---------------------------------------------------------------- the safe way
print("--- the safe extraction: iterate and filter on type ---")
text = "".join(block.text for block in message.content if block.type == "text")
print(text)
print()

print("Lesson: never index into `content` by position. Filter by block type,")
print("and decide whether the turn is finished from `stop_reason`.")

# NOTES FROM THE COURSE
# - max_tokens is a ceiling, not a goal. Hitting it truncates mid-thought,
#   and stop_reason becomes "max_tokens" — which is NOT "done".
# - Two message roles: "user" (human) and "assistant" (Claude). You build the
#   history yourself; the API is stateless and holds no session for you.
# - The course writes .env as ANTHROPIC_API_KEY="key" with quotes. python-dotenv
#   strips them, but a shell `source` of that file keeps them and auth then
#   fails. This repo's .env is written unquoted so both paths work.
