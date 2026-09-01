"""
Exercise 13 — code based grading.

Course C, section: "Code based grading".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287737

WHAT THIS TEACHES
    The two criteria a model grader cannot be trusted with — FORMAT (only
    code, no prose) and VALID SYNTAX — are mechanically checkable, so check
    them mechanically: json.loads / ast.parse / re.compile the output and
    score 10 if it parses, 0 if it does not. The dataset's "format" field
    (added in exercise 10) says which parser to use.

    Three changes over exercise 12:
      1. grade_syntax()  — a code grader beside the model grader
      2. a stricter prompt — "Respond only with Python, JSON, or a plain
         Regex", "Do not add any comments or commentary or explanation" —
         plus a "```code" prefill so the reply starts inside a fence without
         naming the language, and stop_sequences=["```"] to end it
      3. the final score is the average of the two graders

    One parser covers both criteria: if the model wraps the code in prose,
    the parse fails, so format violations and syntax errors score the same 0.

EXAM LINK
    D4 — "deterministic over probabilistic when stakes are high", applied to
    grading itself: syntax is a fact, so a parser judges it, not a model.
    The model grader keeps only what code cannot check: task following.

INTEGRATION NOTE — the guard had to change with the prompt
    Exercise 12 refused to grade any turn that did not end with
    stop_reason == "end_turn". This exercise's prefill + stop_sequences
    makes "stop_sequence" the SUCCESS path — the model is cut off at the
    closing fence deliberately. Same field, same value, opposite meaning to
    exercise 10's warning: what a stop_reason MEANS depends on the request
    that produced it. A guard is part of the prompt design, not around it.

RUN
    From the repo root. Needs dataset.json from exercise 10.
        .venv/bin/python academy/course-c-claude-api/exercises/13-code-based-grading.py

    MEASURED 1 Sep 2026, claude-haiku-4-5, two consecutive runs:
        run 1: 8.0, 8.5, 8.5      -> average 8.33 over 3/3 cases (16s)
        run 2: n/a, 9.0, 8.25     -> average 8.62 over 2/3 cases (11s) + WARNING
    Syntax was 10/10 on every graded case, and the v2 prompt also made the
    model FASTER: ~1-3s per solve vs ~10s in exercise 12, because bare code
    is far shorter than the ~600-word essays the v1 prompt produced.

    RUN 2'S UNGRADED CASE — a new intermittent failure worth keeping
        stop=stop_sequence, 0 chars. The model sometimes reacts to the odd
        "```code" prefill by CLOSING the fence immediately (to reopen a
        proper ```json one), and the stop sequence fires before any code is
        written. Note stop_reason held its "success" value — the same value
        as every graded case — so stop_reason alone cannot distinguish
        "closed the fence after the code" from "closed it before". The
        emptiness check in the guard is what caught it, and the case was
        excluded, not scored 0 (exercise 12's rule).
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


# ---------------------------------------------------------------- pipeline
def run_prompt(test_case):
    """Merges the prompt and test case input, then returns the result.

    v2 of the prompt: explicit format rules, plus the lesson's "```code"
    prefill — the model continues from inside a fence, so the reply is bare
    code with no language tag to strip, and stop_sequences ends it at the
    closing fence. Prefill works because the model under test is Haiku;
    on Opus/Sonnet 5 this exact request 400s (exercises 08, 10)."""
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


# ------------------------------------------------------------ code grader
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
    """Dispatches on the dataset's "format" field. Binary by design: code
    either parses or it does not — there is no 6/10 syntax."""
    fmt = test_case["format"]
    if fmt == "json":
        return validate_json(output)
    elif fmt == "python":
        return validate_python(output)
    elif fmt == "regex":
        return validate_regex(output)
    raise ValueError(f"unknown format in dataset: {fmt!r}")


# ----------------------------------------------------------- model grader
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
    """Unchanged from exercise 12: a schema, not prefill, because the grader
    quotes regex solutions and prefill cannot guarantee well-formed JSON."""
    messages = []
    add_user_message(messages, EVAL_PROMPT.format(task=test_case["task"], solution=output))
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

    # With prefill + stop_sequences, "stop_sequence" IS the completed turn —
    # the model closed its fence and we cut it there. "end_turn" is also fine
    # (it finished without a closing fence). Anything else — max_tokens, an
    # empty reply — is still a pipeline failure and must not be graded.
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

    syntax_score = grade_syntax(output, test_case)           # instant, free
    print(f"{label}  syntax ({test_case['format']}): {syntax_score}/10", flush=True)

    started = time.perf_counter()
    model_grade = grade_by_model(test_case, output)
    print(f"{label}  model grade in {time.perf_counter() - started:4.1f}s "
          f"-> {model_grade['score']}/10", flush=True)

    # Merge: equal weight to content quality and technical correctness. The
    # syntax grader is binary, so a parse failure costs exactly 5 points here
    # — weight it higher if valid code matters more than a good review.
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
dataset = json.loads(DATASET_PATH.read_text())
results = run_eval(dataset)

for result in results:
    score = "n/a" if result["score"] is None else f"{result['score']}/10"
    syntax = "n/a" if result["syntax_score"] is None else f"{result['syntax_score']}/10"
    print(f"\n--- combined {score} (syntax {syntax})")
    print(f"task:       {result['test_case']['task'][:90]}")
    print(f"output len: {len(result['output'])} chars")
    print(f"reasoning:  {result['reasoning'][:180]}")
    print(f"weaknesses: {result['weaknesses']}")

# NOTES FROM THE COURSE
# - Code grading covers Format and Valid Syntax; the model grader keeps Task
#   Following. Together they cover all three criteria from exercise 12.
# - Each validator parses with the real parser for its language and returns
#   10 or 0 — nothing in between.
# - The "```code" prefill starts the reply inside a fence without committing
#   to a language; the closing "```" is the stop sequence.
# - Final score = (model_score + syntax_score) / 2. Adjust the weights when
#   one criterion matters more.
# - The baseline number is not good or bad in itself; the point is having a
#   quantitative target so prompt changes are measured, not felt.
#
# WORTH KNOWING (Domain 4)
# - This is the decision-rule habit in miniature: syntax is mechanically
#   checkable, so a deterministic parser grades it; task following is not,
#   so a model does. Never spend a probabilistic judge on a deterministic
#   question.
# - The code grader is also immune to the exercise-12 confabulation failure:
#   a parser cannot invent a review of an empty string — it just returns 0.
# - Averaging graders hides which one moved. Keeping syntax_score in the
#   result (printed beside the combined score) preserves the diagnosis.
