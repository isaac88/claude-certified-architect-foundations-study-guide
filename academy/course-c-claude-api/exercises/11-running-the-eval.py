"""
Exercise 11 — running the eval.

Course C, section: "Running the eval".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287743

WHAT THIS TEACHES
    The core eval pipeline, in three functions:

        run_prompt(test_case)    merge the test case into the prompt, call Claude
        run_test_case(test_case) call run_prompt, then grade the output
        run_eval(dataset)        loop the dataset, collect the results

    Each result is {output, test_case, score}. Grading is still a hardcoded
    10 — the next sections replace it. The pipeline is deliberately finished
    before the grader exists, so the shape is testable on its own.

    The prompt is intentionally bare, with no formatting instructions, so
    Claude answers verbosely. That verbosity is the problem the eval is
    meant to expose.

DIVERGENCE from the lesson, verified 1 Sep 2026
    chat() returns the message, not content[0].text — that indexing raises
    whenever the first block is thinking or tool_use (exercises 02, 03).

RUN
    From the repo root. Needs dataset.json from exercise 10.
        .venv/bin/python academy/course-c-claude-api/exercises/11-running-the-eval.py
"""

import json
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-haiku-4-5"   # the course uses Haiku throughout

DATASET_PATH = Path(__file__).parent / "dataset.json"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def chat(messages, system=None, model=MODEL, stop_sequences=None):
    params = {"model": model, "max_tokens": 2000, "messages": messages}
    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    return client.messages.create(**params)


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


# ---------------------------------------------------------------- the pipeline
def run_prompt(test_case):
    """Merges the prompt and test case input, then returns the result."""
    prompt = f"""
Please solve the following task:

{test_case["task"]}
"""
    messages = []
    add_user_message(messages, prompt)
    return text_of(chat(messages))


def run_test_case(test_case):
    """Calls run_prompt, then grades the result."""
    output = run_prompt(test_case)

    # TODO — grading. Replaced in the next sections.
    score = 10

    return {"output": output, "test_case": test_case, "score": score}


def run_eval(dataset):
    """Loads the dataset and calls run_test_case with each case."""
    results = []
    for test_case in dataset:
        results.append(run_test_case(test_case))
    return results


# ---------------------------------------------------------------- run
dataset = json.loads(DATASET_PATH.read_text())

started = time.perf_counter()
results = run_eval(dataset)
elapsed = time.perf_counter() - started

print(json.dumps(results, indent=2))
print(f"\n{len(results)} test cases in {elapsed:.1f}s "
      f"({elapsed / len(results):.1f}s each, run sequentially)")

# NOTES FROM THE COURSE
# - This is the majority of what an eval pipeline does. The complexity lives in
#   the details: better prompts, real grading, performance.
# - Each result keeps the output, the test case that produced it, and the score.
#   Keeping the test case alongside the output is what makes a failure
#   diagnosable later.
# - The bare prompt produces verbose output — that is the finding, not a bug.
#   The eval exists to make it visible.
#
# WORTH KNOWING (Domain 4)
# - The loop is sequential, so wall time grows linearly with the dataset. The
#   calls are independent, so this is the obvious place for parallelism — the
#   course returns to it.
# - The MODEL is a control variable too, not just the dataset. Change the model
#   and the prompt at the same time and a score change tells you nothing about
#   either.
