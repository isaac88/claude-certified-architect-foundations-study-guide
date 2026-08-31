"""
Exercise 04 — chat bot.

Course C, section: "Chat Bot Exercise".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287727

THE BRIEF (from the slide)
    Make a chat bot using the three helper functions we just put together.
      1. Prompt the user for input with the built-in `input` function
      2. Add it to a list of messages
      3. Call the API
      4. Add the generated text to the list of messages
      5. Print the generated text
      6. Repeat from #1

WHAT THIS TEACHES
    The loop is the whole point. Because the API is stateless, the bot's
    "memory" is nothing more than the `messages` list surviving across
    iterations. Step 4 is what makes it a conversation rather than a series
    of unrelated questions — drop it and every turn starts from nothing.

    Watch the input-token count printed each turn. It climbs, because every
    request resends the entire history. That is the cost of statelessness.

EXAM LINK (Domain 1.1, Domain 1.7)
    This is the simplest possible agentic loop: gather input, call, append,
    repeat. Swap the human at step 1 for `stop_reason` and tool execution and
    you have the agent loop from task 1.1. The exit condition here is the
    user typing "exit"; in 1.1 it is `stop_reason == "end_turn"`. In both
    cases the loop ends on an explicit signal, never on a guess.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/04-chat-bot-exercise.py

    Type "exit" (or an empty line, or Ctrl-D) to quit.
"""

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-opus-5"


# ---------------------------------------------------------------- the three helpers
def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, content):
    # `content` may be a string or the response's block list. Passing the block
    # list is always correct — see reference/history-replay-with-tools.py.
    messages.append({"role": "assistant", "content": content})


def chat(messages):
    return client.messages.create(model=MODEL, max_tokens=1000, messages=messages)


def text_of(message):
    """Every text block, joined. Never `content[0].text`."""
    return "".join(b.text for b in message.content if b.type == "text")


# ---------------------------------------------------------------- the loop
def main():
    messages = []
    total_in = total_out = 0

    print("Chat bot. Type 'exit', an empty line, or Ctrl-D to quit.\n")

    while True:
        # 1. prompt the user
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

        if user_input.lower() in {"exit", "quit", ""}:
            print("bye")
            break

        # 2. add it to the list of messages
        add_user_message(messages, user_input)

        # 3. call the API
        message = chat(messages)

        # 4. add the generated response to the list of messages
        add_assistant_message(messages, message.content)

        # 5. print it
        answer = text_of(message)
        print(f"claude> {answer}")

        total_in += message.usage.input_tokens
        total_out += message.usage.output_tokens
        print(
            f"        [turn: {message.usage.input_tokens} in / "
            f"{message.usage.output_tokens} out | "
            f"session: {total_in} in / {total_out} out | "
            f"{len(messages)} messages]\n"
        )
        # 6. repeat

    if messages:
        print(f"\nconversation ended with {len(messages)} messages, "
              f"{total_in} input tokens billed in total.")
        print("Input tokens grew each turn because the whole history is resent")
        print("every time. Prompt caching is the first fix for that.")


if __name__ == "__main__":
    main()

# NOTES FROM THE COURSE
# - The three helpers do all the work; the loop just sequences them.
# - Step 4 is the one people forget. Without it the bot answers each question
#   in isolation and looks broken in a way that is hard to spot in short tests.
#
# DIVERGENCES from the course
# 1. `chat()` returns the message, not `message.content[0].text` — that
#    indexing raises whenever the first block is thinking or tool_use, and the
#    block mix varies run to run even for a fixed prompt.
# 2. `add_assistant_message` is given `message.content` (the blocks) rather
#    than the extracted string. Same result for plain chat, and it is the only
#    form that keeps working once tools are involved.
