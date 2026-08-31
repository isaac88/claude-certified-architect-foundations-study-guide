"""
Exercise 01 — a single Messages API request.

Course C: Building with the Claude API.

WHAT THIS TEACHES
    Every Claude call is one POST to /v1/messages. There is no separate
    "chat" endpoint and no separate "tools" endpoint. Tools, structured
    output and thinking are all parameters on this one call.

EXAM LINK (Domain 1)
    `response.content` is a LIST of blocks, not a string. Getting used to
    indexing it here is what makes the 1.1 premature-stop bug obvious later.

RUN
    From the repo root (single venv, the one your IDE selects):
        .venv/bin/python academy/course-c-claude-api/exercises/01-first-request.py
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

response = client.messages.create(
    model="claude-opus-5",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "In two sentences, what is an agentic loop?"}
    ],
)

# The response is a Message object. Inspect the parts that matter.
print("stop_reason:", response.stop_reason)
print("block types:", [block.type for block in response.content])
print("usage:", response.usage.input_tokens, "in /", response.usage.output_tokens, "out")
print()

for block in response.content:
    if block.type == "text":
        print(block.text)

# NOTES FROM THE COURSE (fill in as you watch)
# -
#
# FIRST REAL RUN — 31 Aug 2026, claude-opus-5:
#
#     stop_reason: end_turn
#     block types: ['thinking', 'text']
#     usage: 21 in / 161 out
#
# content[0] was a THINKING block, not text. Opus 5 runs adaptive thinking by
# default, so reasoning arrives as its own block before the answer.
#
# This is the 1.1 lesson, harder than the notes put it: content[0].type is not
# merely "often" wrong to branch on — its value depends on the model, the
# thinking config and the turn. It can be thinking, text or tool_use. There is
# no position in `content` you may safely assume. Branch on stop_reason.
