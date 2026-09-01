"""
Exercise 10 — generating test datasets.

Course C, section: "Generating test datasets".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    (paste the section URL here)

WHAT THIS TEACHES
    Step one of an eval pipeline is the DATASET: the inputs the prompt will be
    run against. Generate them with a cheap fast model — Haiku — because
    producing test inputs is not the hard part. Then save them to a file.

    Getting parseable JSON back uses prefilling plus a stop sequence, exactly
    as the lesson does:
        add_assistant_message(messages, "```json")   # Claude thinks it opened a fence
        chat(messages, stop_sequences=["```"])       # stop when it tries to close it

    The prompt being evaluated (version 1, from the lesson) is kept here for
    the next section, which scores it:
        "Please provide a solution to the following task: {task}"

NOTE ON PREFILL, verified 1 Sep 2026
    Prefill still works on claude-haiku-4-5, which is the model doing the
    generating here — so the lesson's technique runs as written. It does NOT
    work on the current top-tier models:
        claude-haiku-4-5  prefill -> OK, stop_reason=stop_sequence
        claude-opus-5     prefill -> 400 "This model does not support
                                     assistant message prefill."
    So keep this pattern for Haiku-generated data, but do not carry it to a
    prompt running on Opus or Sonnet 5 — see exercise 08 for the replacement.

DIVERGENCES from the lesson, verified 1 Sep 2026
    temperature=1.0   removed from anthropic SDK 1.2.0 -> TypeError (ex. 06)
    content[0].text   raises when the first block is thinking/tool_use (ex. 02, 03)

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/10-generating-test-datasets.py
"""

import json
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-haiku-4-5"              # the course uses Haiku throughout
GENERATOR_MODEL = "claude-haiku-4-5"    # cheap, fast, and still accepts prefill

DATASET_PATH = Path(__file__).parent / "dataset.json"

# The prompt under test — version 1, verbatim from the lesson.
PROMPT_V1 = """
Please provide a solution to the following task:
{task}
"""


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, system=None, model=MODEL, stop_sequences=None):
    """The lesson's chat(), minus `temperature` (removed from the SDK) and
    returning the message rather than content[0].text."""
    params = {"model": model, "max_tokens": 2000, "messages": messages}
    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    return client.messages.create(**params)


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


GENERATE_PROMPT = """
Generate an evaluation dataset for a prompt evaluation. The dataset will be used
to evaluate prompts that generate Python, JSON, or Regex specifically for
AWS-related tasks. Generate an array of JSON objects, each representing a task
that requires Python, JSON, or a Regex to complete. Include a "format" field on
each object saying which of json, python or regex the answer must be.

Example output:
```json
[
  {{
    "task": "Description of task",
    "format": "json" or "python" or "regex"
  }}
]
```

* Focus on tasks that can be solved by writing a single Python function, a
  single JSON object, or a single regex
* Focus on tasks that do not require writing much code

Please generate {n} objects.
"""


def generate_dataset(n=3):
    messages = []
    add_user_message(messages, GENERATE_PROMPT.format(n=n))
    add_assistant_message(messages, "```json")          # prefill: mid-fence
    message = chat(messages, model=GENERATOR_MODEL, stop_sequences=["```"])
    return json.loads(text_of(message).strip())         # .strip() — the reply opens with \n


dataset = generate_dataset(3)

for i, item in enumerate(dataset, 1):
    print(f"{i}. {item['task']}")

DATASET_PATH.write_text(json.dumps(dataset, indent=2) + "\n")
print(f"\nwrote {DATASET_PATH.name} with {len(dataset)} tasks")

# NOTES FROM THE COURSE
# - An eval dataset is just inputs. For each (prompt, input) pair you run the
#   prompt and analyse the result.
# - Generate it with a cheap fast model. Haiku returns blocks ['text'] with no
#   thinking block, so it is cheaper per call as well as faster.
# - Prefill "```json" + stop_sequences ["```"] gives JSON with no fence and no
#   commentary, so json.loads() works after a .strip().
# - Save it to a file to load in later sections.
#
# WORTH KNOWING (Domain 4)
# - The dataset is the experimental CONTROL. An eval compares prompt v1 with
#   v2; if the inputs change between runs, a score change tells you nothing.
#   Once the next section starts scoring, stop regenerating this file.
# - stop_reason here is "stop_sequence", not "end_turn" — the model was cut off
#   deliberately. Never treat a cut-off turn as a completed one (Domain 1.1).
