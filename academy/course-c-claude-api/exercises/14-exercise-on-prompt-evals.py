"""
Exercise 14 — exercise on prompt evals.

Course C, section: "Exercise on prompt evals".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287738
    Spec taken from the official 001_prompt_evals_complete.ipynb — the delta
    over exercises 10-13 is exactly one field.

WHAT THIS TEACHES
    The grader in exercises 12-13 invented its own rubric on every call —
    ask it to judge "a Python function to validate a bucket name" and it
    decides, per run, whether docstrings or type checks matter. This
    exercise pins the rubric: dataset generation now also produces a
    "solution_criteria" string per test case, and grade_by_model receives it
    in a <criteria> block. The rubric becomes part of the DATASET — fixed at
    generation time, identical on every run and for every prompt version.

    Two changes, both from the notebook:
      1. generate_dataset() asks for "solution_criteria": "Key criteria for
         evaluating the solution" on each object
      2. EVAL_PROMPT gains:  Criteria you should use to evaluate the
         solution: <criteria>{solution_criteria}</criteria>

CONTROL RESET — deliberate, and worth noticing
    Regenerating dataset.json breaks exercise 10's rule ("once scoring
    starts, stop regenerating") because the new field can only come from
    generation. The 8.3-8.6 baseline of exercise 13 is therefore RETIRED:
    new cases, new rubric, new baseline. Scores before and after this file
    must never be compared. Exercises 12-13 still run against the new file —
    they simply ignore the extra field — but their docstring numbers were
    measured against the old control.

EXAM LINK
    D4 — explicit, testable criteria beat vague instruction (same principle
    as exercise 05's system prompt, applied to the JUDGE). Moving the rubric
    into the dataset makes the grader consistent across runs and across
    prompt versions — without it, a score change can mean the grader changed
    its mind, not that the prompt got better or worse.

RUN
    From the repo root. Regenerates dataset.json (with solution_criteria),
    then runs the full eval against it.
        .venv/bin/python academy/course-c-claude-api/exercises/14-exercise-on-prompt-evals.py

    MEASURED 1 Sep 2026, claude-haiku-4-5, first run on the new control:
        8.5, 8.75, 7.75  -> average 8.33 over 3/3 cases (13s), syntax 10/10
        (the notebook's own run: 8.17 — same ballpark, different cases)

    THE CRITERIA VISIBLY WORKED on case 3: its solution_criteria demanded
    case-insensitive level matching, the generated function compared
    uppercase strings only, and the grader's reasoning cited that criterion
    by name ("it fails to meet the criterion of case-insensitive matching")
    and scored it lowest, 5.5. That judgement could not have been RELIED ON
    in exercises 12-13 — an improvised rubric only sometimes thinks of case
    sensitivity. A pinned rubric fails the same way every time.
"""

import ast
import json
import re
import time
from pathlib import Path
from statistics import mean

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-haiku-4-5"             # the model under evaluation (as the course does)
GENERATOR_MODEL = "claude-haiku-4-5"   # writes the dataset; accepts prefill
GRADER_MODEL = "claude-haiku-4-5"      # judges task following

DATASET_PATH = Path(__file__).parent / "dataset.json"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, system=None, model=MODEL, stop_sequences=None, max_tokens=4000,
         output_schema=None):
    params = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        params["system"] = system
    if stop_sequences:
        params["stop_sequences"] = stop_sequences
    if output_schema:
        params["output_config"] = {"format": {"type": "json_schema", "schema": output_schema}}
    return client.messages.create(**params)


def text_of(message):
    return "".join(b.text for b in message.content if b.type == "text")


# ---------------------------------------------------- step 1: the dataset
GENERATE_PROMPT = """
Generate an evaluation dataset for a prompt evaluation. The dataset will be used
to evaluate prompts that generate Python, JSON, or Regex specifically for
AWS-related tasks. Generate an array of JSON objects, each representing a task
that requires Python, JSON, or a Regex to complete.

Example output:
```json
[
  {{
    "task": "Description of task",
    "format": "json" or "python" or "regex",
    "solution_criteria": "Key criteria for evaluating the solution"
  }}
]
```

* Focus on tasks that can be solved by writing a single Python function, a
  single JSON object, or a regular expression.
* Focus on tasks that do not require writing much code

Please generate {n} objects.
"""


def generate_dataset(n=3):
    """As exercise 10, plus solution_criteria — the rubric is authored HERE,
    once, not improvised by the grader on every call."""
    messages = []
    add_user_message(messages, GENERATE_PROMPT.format(n=n))
    add_assistant_message(messages, "```json")          # prefill: fine on Haiku
    message = chat(messages, model=GENERATOR_MODEL, stop_sequences=["```"])
    return json.loads(text_of(message).strip())


# ---------------------------------------------------- step 2: the pipeline
def run_prompt(test_case):
    """Unchanged from exercise 13 (v2 prompt + "```code" prefill)."""
    prompt = f"""
Please solve the following task:

{test_case["task"]}

* Respond only with Python, JSON, or a plain Regex
* Do not add any comments or commentary or explanation
"""
    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, "```code")
    return chat(messages, stop_sequences=["```"])


def validate_json(text):
    try:
        json.loads(text.strip())
        return 10
    except json.JSONDecodeError:
        return 0


def validate_python(text):
    try:
        ast.parse(text.strip())
        return 10
    except SyntaxError:
        return 0


def validate_regex(text):
    try:
        re.compile(text.strip())
        return 10
    except re.error:
        return 0


def grade_syntax(output, test_case):
    fmt = test_case["format"]
    if fmt == "json":
        return validate_json(output)
    elif fmt == "python":
        return validate_python(output)
    elif fmt == "regex":
        return validate_regex(output)
    raise ValueError(f"unknown format in dataset: {fmt!r}")


EVAL_PROMPT = """
You are an expert AWS code reviewer. Your task is to evaluate the following
AI-generated solution.

Original Task:
<task>
{task}
</task>

Solution to Evaluate:
<solution>
{solution}
</solution>

Criteria you should use to evaluate the solution:
<criteria>
{criteria}
</criteria>

Output Format
Provide your evaluation as a structured JSON object with the following fields,
in this specific order:
- "strengths": An array of 1-3 key strengths
- "weaknesses": An array of 1-3 key areas for improvement
- "reasoning": A concise explanation of your overall assessment
- "score": A number between 1-10

Respond with JSON. Keep your response concise and direct.
Example response shape:
{{
    "strengths": string[],
    "weaknesses": string[],
    "reasoning": string,
    "score": number
}}
"""


GRADE_SCHEMA = {
    "type": "object",
    "properties": {
        "strengths": {"type": "array", "items": {"type": "string"}},
        "weaknesses": {"type": "array", "items": {"type": "string"}},
        "reasoning": {"type": "string"},
        "score": {"type": "number"},
    },
    "required": ["strengths", "weaknesses", "reasoning", "score"],
    "additionalProperties": False,
}


def grade_by_model(test_case, output):
    """The notebook's grader plus the two standing local decisions: a schema
    instead of prefill (regex solutions break prefilled JSON — exercise 12),
    and an unparseable reply returns a marker instead of raising."""
    messages = []
    add_user_message(messages, EVAL_PROMPT.format(
        task=test_case["task"],
        solution=output,
        criteria=test_case["solution_criteria"],
    ))
    message = chat(messages, model=GRADER_MODEL, output_schema=GRADE_SCHEMA)

    try:
        return json.loads(text_of(message).strip())
    except json.JSONDecodeError as exc:                      # belt and braces
        return {
            "score": None,
            "reasoning": f"GRADER OUTPUT UNPARSEABLE — {exc}",
            "strengths": [],
            "weaknesses": ["grader reply was not valid JSON"],
        }


def run_test_case(test_case, index=None, total=None):
    label = f"[{index}/{total}] " if index else ""
    print(f"{label}running:  {test_case['task'][:64]}...", flush=True)

    started = time.perf_counter()
    message = run_prompt(test_case)
    output = text_of(message).strip()
    print(f"{label}  solved in {time.perf_counter() - started:4.1f}s "
          f"(stop={message.stop_reason}, {len(output)} chars)", flush=True)

    # stop_sequence is the success value here (prefill closes at the fence),
    # but it can also mean the fence closed BEFORE any code (exercise 13,
    # run 2) — hence the emptiness check.
    if message.stop_reason not in ("stop_sequence", "end_turn") or not output:
        print(f"{label}  NOT GRADED (score=None)", flush=True)
        return {
            "output": output,
            "test_case": test_case,
            "score": None,
            "syntax_score": None,
            "reasoning": f"NOT GRADED — stop_reason={message.stop_reason}, "
                         f"{len(output)} chars of text",
            "strengths": [],
            "weaknesses": ["incomplete turn; raise max_tokens or retry"],
        }

    syntax_score = grade_syntax(output, test_case)
    print(f"{label}  syntax ({test_case['format']}): {syntax_score}/10", flush=True)

    started = time.perf_counter()
    model_grade = grade_by_model(test_case, output)
    print(f"{label}  model grade in {time.perf_counter() - started:4.1f}s "
          f"-> {model_grade['score']}/10", flush=True)

    if model_grade["score"] is None:
        score = None                                          # ungraded, not 0
    else:
        score = (model_grade["score"] + syntax_score) / 2

    return {
        "output": output,
        "test_case": test_case,
        "score": score,
        "syntax_score": syntax_score,
        "reasoning": model_grade["reasoning"],
        "strengths": model_grade["strengths"],
        "weaknesses": model_grade["weaknesses"],
    }


def run_eval(dataset):
    results = []
    started = time.perf_counter()

    for i, test_case in enumerate(dataset, 1):
        results.append(run_test_case(test_case, i, len(dataset)))

    elapsed = time.perf_counter() - started

    graded = [r["score"] for r in results if r["score"] is not None]
    ungraded = len(results) - len(graded)

    if graded:
        print(f"\nAverage score: {mean(graded):.2f} over {len(graded)}/{len(results)} cases"
              f"   ({elapsed:.0f}s)")
    else:
        print(f"\nNo cases could be graded ({elapsed:.0f}s)")
    if ungraded:
        print(f"WARNING: {ungraded} case(s) not graded — pipeline failure, not a quality signal")

    return results


# ---------------------------------------------------------------- run
print("generating dataset (with solution_criteria)...", flush=True)
dataset = generate_dataset(3)
DATASET_PATH.write_text(json.dumps(dataset, indent=2) + "\n")
print(f"wrote {DATASET_PATH.name} with {len(dataset)} tasks — NEW CONTROL, "
      f"old baselines retired\n", flush=True)

results = run_eval(dataset)

for result in results:
    score = "n/a" if result["score"] is None else f"{result['score']}/10"
    syntax = "n/a" if result["syntax_score"] is None else f"{result['syntax_score']}/10"
    print(f"\n--- combined {score} (syntax {syntax})")
    print(f"task:       {result['test_case']['task'][:90]}")
    print(f"criteria:   {result['test_case']['solution_criteria'][:90]}")
    print(f"reasoning:  {result['reasoning'][:180]}")
    print(f"weaknesses: {result['weaknesses']}")

# NOTES FROM THE COURSE (via the complete notebook)
# - The exercise's whole delta is solution_criteria: authored at dataset
#   generation, consumed by the grader in a <criteria> block.
# - The notebook's own run scored 8.17 over its 3 cases.
# - Everything else — v2 prompt, "```code" prefill, validators, 50/50
#   combined score — is exercise 13 unchanged.
#
# WORTH KNOWING (Domain 4)
# - Without per-case criteria the grader IS part of the noise: it improvises
#   a rubric per call, so run-to-run score drift mixes "the prompt changed"
#   with "the judge changed its mind". Fixing the rubric in the dataset
#   removes the second source. Control the judge, not just the inputs.
# - The criteria are still model-authored — the generator's opinion of what
#   matters, frozen. A bad criterion is now CONSISTENTLY bad, which is still
#   better for measurement: consistent bias beats random bias in an eval,
#   because deltas between prompt versions remain meaningful.
# - This is the last stop before human-authored rubrics: real evals promote
#   criteria review to a human step precisely because everything downstream
#   inherits them.
