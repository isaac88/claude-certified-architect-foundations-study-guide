"""
Why the assistant history must keep BLOCKS, not just text.

Not a course exercise — written by the instructor-agent. The course's
"Multi-Turn Conversations" section covers plain chat only; this is the
consequence of its `add_assistant_message(messages, answer)` helper once
tools enter the picture, which is where Domain 1 lives.

WHAT THIS SHOWS
    1. A tool turn can return NO text block at all (`blocks: ['tool_use']`),
       so `message.content[0].text` raises.
    2. A string-only assistant history therefore stores '' and loses the
       tool_use block.
    3. The next request is then rejected with HTTP 400 — a tool_result must
       pair with a tool_use block in the previous message.
    4. The identical request with `response.content` preserved succeeds.

EXAM LINK (Domain 1.1)
    This is the mechanical reason the agentic loop resends full history. The
    loop is not "resend for context" — the pairing is a hard API requirement.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/reference/history-replay-with-tools.py
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-opus-5"

TOOLS = [{
    "name": "get_weather",
    "description": "Get the current weather for a city.",
    "input_schema": {
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
}]


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


opening = {"role": "user", "content": "What's the weather in Paris? Use the tool."}
tool_turn = client.messages.create(
    model=MODEL, max_tokens=1000, tools=TOOLS, messages=[opening]
)

print("stop_reason:", tool_turn.stop_reason)
print("blocks:     ", [b.type for b in tool_turn.content])
tool_use = next(b for b in tool_turn.content if b.type == "tool_use")
print(f"tool_use:    id={tool_use.id} name={tool_use.name} input={tool_use.input}")
print()
print("There may be NO text block here. `content[0].text` raises on this turn.")
print()

lossy = text_of(tool_turn)
print(f"a string-only history stores: {lossy!r}  <- tool_use block gone")
print()

print("--- tool_result sent with the LOSSY history ---")
try:
    client.messages.create(
        model=MODEL, max_tokens=1000, tools=TOOLS,
        messages=[
            opening,
            {"role": "assistant", "content": lossy or "..."},
            {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tool_use.id, "content": "18C, sunny"}
            ]},
        ],
    )
    print("no error raised")
except Exception as exc:
    print(f"{type(exc).__name__}: {str(exc)[:240]}")
print()

print("--- the same call with BLOCKS preserved ---")
recovered = client.messages.create(
    model=MODEL, max_tokens=1000, tools=TOOLS,
    messages=[
        opening,
        {"role": "assistant", "content": tool_turn.content},   # blocks, not a string
        {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": tool_use.id, "content": "18C, sunny"}
        ]},
    ],
)
print("stop_reason:", recovered.stop_reason)
print(text_of(recovered))
print()
print("Rule: append `response.content` to the history, never just the text.")
