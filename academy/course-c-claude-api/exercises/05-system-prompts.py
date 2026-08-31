"""
Exercise 05 — system prompts.

Course C, section: "System prompts".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287733

WHAT THIS TEACHES
    `system` is a TOP-LEVEL parameter on messages.create() — a plain string,
    not an entry in the `messages` list. It tells Claude how to behave, and
    Claude answers as someone in that role would.

    The lesson's example: the same maths question, answered as a solver vs
    answered as a patient tutor. Same model, same question, same history —
    only the system prompt differs.

    Also: a reusable `chat(messages, system=None)`. The API rejects
    `system=None`, so the key must be omitted rather than passed as None.

EXAM LINK (Domain 4)
    Explicit criteria beat vague instruction. "Do not directly answer" and
    "guide them step by step" are testable; "be a good tutor" is not. Note
    also that the system prompt is the most stable part of a request, which
    makes it the natural thing to cache — see the note at the foot of this
    file.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/05-system-prompts.py
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-opus-5"


# ---------------------------------------------------------------- helpers
def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, content):
    messages.append({"role": "assistant", "content": content})


def chat(messages, system=None):
    """The course's flexible version. `system` is omitted entirely when not
    given, because the API rejects system=None.

    Returns the message, not content[0].text — that indexing raises whenever
    the first block is thinking or tool_use."""
    params = {
        "model": MODEL,
        "max_tokens": 1000,
        "messages": messages,
    }

    if system:
        params["system"] = system

    return client.messages.create(**params)


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


QUESTION = "How do I solve 5x + 2 = 3 for x?"

SYSTEM_PROMPT = """
You are a patient math tutor.
Do not directly answer a student's questions.
Guide them to a solution step by step.
"""


# ---------------------------------------------------------------- without
print("=" * 70)
print("WITHOUT a system prompt")
print("=" * 70)

messages = []
add_user_message(messages, QUESTION)
plain = chat(messages)
print(text_of(plain))
print()


# ---------------------------------------------------------------- with
print("=" * 70)
print("WITH the math-tutor system prompt")
print("=" * 70)

messages = []
add_user_message(messages, QUESTION)
tutored = chat(messages, system=SYSTEM_PROMPT)
print(text_of(tutored))
print()


# ---------------------------------------------------------------- the mechanics
print("=" * 70)
print("MECHANICS")
print("=" * 70)
print("`system` is a top-level parameter, NOT a message in the list.")
print("The messages list was identical in both calls:")
print(f"  {messages}")
print()
print(f"tokens without system: {plain.usage.input_tokens} in / {plain.usage.output_tokens} out")
print(f"tokens with system:    {tutored.usage.input_tokens} in / {tutored.usage.output_tokens} out")
print()
print("The system prompt costs input tokens on EVERY request, since it is")
print("resent each time alongside the history.")
print()
print("Proof that system=None must be omitted rather than passed:")
try:
    client.messages.create(
        model=MODEL, max_tokens=64, system=None,
        messages=[{"role": "user", "content": "hi"}],
    )
    print("  no error raised")
except Exception as exc:
    print(f"  {type(exc).__name__}: {str(exc)[:200]}")

# NOTES FROM THE COURSE
# - System prompts shape tone, style and approach. Claude answers as someone in
#   the stated role would.
# - They keep Claude on task: the tutor prompt stops it short-circuiting to the
#   answer even though it obviously knows it.
# - `if system: params["system"] = system` — build the kwargs dict conditionally.
#   The API will not accept system=None.
#
# WORTH KNOWING (beyond this lesson)
# - Claude's `system` is a top-level string, NOT a {"role": "system"} entry in
#   `messages`. Other vendors' APIs do it the other way; the exam cares.
# - Caching renders a request in the order tools -> system -> messages, so the
#   system prompt sits near the front of the cacheable prefix. Keep it byte
#   stable: interpolating a timestamp or a per-request id into it silently
#   destroys cache hits for everything after it.
#
# DIVERGENCE from the course
# 1. `chat()` returns the message rather than `message.content[0].text`. The
#    conditional-kwargs pattern itself is correct and worth keeping.
