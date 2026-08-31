"""
Exercise 03 — multi-turn conversations.

Course C, section: "Multi-Turn Conversations".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    (paste the section URL here)

WHAT THIS TEACHES
    The API is STATELESS. Claude stores nothing between requests. The
    `messages` list you send IS the conversation — you own it, you rebuild
    it every call, and anything you leave out never existed.

    Turn 1 answer -> append it as an "assistant" message -> add the next
    "user" message -> send the whole list again.

EXAM LINK (Domain 1.1 loops, Domain 1.7 session state)
    Statelessness is why the agent loop in 1.1 works the way it does: you
    append results to the history and resend everything.

SCOPE
    Stages 1-2 follow the course section. Stage 3 is a short annotation on the
    course's own `add_assistant_message` helper. Tools are NOT part of this
    lesson — the consequence for tool loops lives in
    reference/history-replay-with-tools.py.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/03-multi-turn-conversations.py
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-opus-5"


# ---------------------------------------------------------------- helpers
def add_user_message(messages, text):
    """Same as the course."""
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, content):
    """The course passes a plain string here. This accepts either a string or
    the response's `content` block list. Always correct; see
    reference/history-replay-with-tools.py for when it becomes essential."""
    messages.append({"role": "assistant", "content": content})


def chat(messages, tools=None):
    """The course returns `message.content[0].text`, which raises on any
    response whose first block is not text (thinking or tool_use). Return the
    whole message and let the caller decide."""
    kwargs = {"model": MODEL, "max_tokens": 1000, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    return client.messages.create(**kwargs)


def text_of(message):
    """Every text block, joined. Never indexes by position."""
    return "".join(b.text for b in message.content if b.type == "text")


# ---------------------------------------------------------------- stage 1
print("=" * 70)
print("STAGE 1 — the problem: no history means no memory")
print("=" * 70)

m = chat([{"role": "user", "content": "Define quantum computing in one sentence"}])
print("turn 1:", text_of(m), "\n")

m = chat([{"role": "user", "content": "Write another sentence"}])
print("turn 2, sent with NO history:")
print(text_of(m)[:300], "...\n")
print("-> Claude says it has nothing to build on. The API remembered nothing.\n")


# ---------------------------------------------------------------- stage 2
print("=" * 70)
print("STAGE 2 — the fix: carry the history yourself")
print("=" * 70)

messages = []
add_user_message(messages, "Define quantum computing in one sentence")
first = chat(messages)
print("turn 1:", text_of(first), "\n")

add_assistant_message(messages, text_of(first))   # course-style: a string
add_user_message(messages, "Write another sentence")
second = chat(messages)
print("turn 2, WITH history:", text_of(second), "\n")

print("the list that produced it:")
for i, msg in enumerate(messages):
    body = msg["content"] if isinstance(msg["content"], str) else f"<{len(msg['content'])} blocks>"
    print(f"  [{i}] {msg['role']:9} {str(body)[:60]}")
print()


# ---------------------------------------------------------------- stage 3
print("=" * 70)
print("STAGE 3 (annotation, beyond the course) — what a string history discards")
print("=" * 70)

blocks = [b.type for b in first.content]
dropped = [b.type for b in first.content if b.type != "text"]
print("blocks Claude actually returned:", blocks)
print("stored by the course's string version:", repr(text_of(first)[:40] + "..."))
print("discarded:", dropped if dropped else "[] — nothing to drop on THIS run")
print()
if not dropped:
    print("Note: adaptive thinking is adaptive. The same prompt returns")
    print("['thinking', 'text'] on some runs and ['text'] on others. That")
    print("non-determinism is the point: content[0].type is not stable even")
    print("for a fixed prompt, so no index into `content` is ever safe.")
    print()
print("Harmless for plain chat. Not harmless once tools appear — see")
print("reference/history-replay-with-tools.py for the live 400.\n")


# NOTES FROM THE COURSE
# - The API is stateless. The messages list IS the conversation. Nothing is
#   stored server-side between requests, so a follow-up with no history is
#   literally a brand-new conversation.
# - Roles alternate user / assistant. You add Claude's own replies back in as
#   "assistant" yourself; the API will not do it for you.
# - Every turn resends the whole history, so input tokens grow with the
#   conversation. That is what prompt caching (and later, compaction and
#   context editing) exists to manage.
#
# DIVERGENCES from the course, all verified live on 31 Aug 2026:
# 1. `chat()` returning `message.content[0].text` raises AttributeError on any
#    turn whose first block is thinking or tool_use. Filter by block type.
# 2. `add_assistant_message(messages, answer)` storing a plain string discards
#    thinking blocks. Harmless here; fatal once tools are involved. Appending
#    `response.content` costs nothing and is always correct.
#    Demonstrated in reference/history-replay-with-tools.py.
