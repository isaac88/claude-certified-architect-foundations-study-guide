"""
Exercise 12 — model based grading.

Course C, section: "Model based grading".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287742

WHAT THIS TEACHES
    Replace the hardcoded score with a real one. A grader takes output and
    returns a measurable signal, usually 1-10.

    Three kinds:
      code graders    programmatic checks — length, forbidden words, syntax
      model graders   another API call judges the output
      human graders   most flexible, slowest

    Evaluation criteria for this prompt:
      Format        only Python, JSON or Regex, no explanation   -> code grader
      Valid syntax  the produced code parses                     -> code grader
      Task following addresses the task, accurately              -> MODEL grader

    The key prompt-engineering move: ask for strengths, weaknesses and
    reasoning ALONGSIDE the score. Without that context models converge on a
    middling ~6 for everything, which carries no signal.

NOTE ON THE ARTICLE vs THE OFFICIAL NOTEBOOK
    The course web page shows the eval prompt with {task} and {solution}
    placeholders and no .format() call. Run verbatim that grades nothing — the
    grader replies "No task description provided" and scores 0. But the
    official notebook (001_prompt_evals_grader.ipynb) uses an f-string, so
    that was a transcription error on the page, not a bug in the course.

    The notebook's prompt is also materially better than the page's, and this
    file uses it: XML <task>/<solution> delimiters, an explicit field order,
    an example response shape, and "Keep your response concise and direct."

NOTE ON THE GRADER MODEL, verified 1 Sep 2026
    The grader uses prefill, which works on claude-haiku-4-5 but 400s on
    claude-opus-5. So the grader runs on Haiku here. That is cheap and fast,
    but a grader is only as discerning as the model behind it — if you want a
    stronger judge, drop prefill for a json_schema (exercise 08).

DIVERGENCE
    chat() returns the message, not content[0].text (exercises 02, 03).

RUN
    From the repo root. Needs dataset.json from exercise 10.
        .venv/bin/python academy/course-c-claude-api/exercises/12-model-based-grading.py

    MEASURED 1 Sep 2026, claude-haiku-4-5, two consecutive runs:
        run 1: 7.5, 8, 6.5  -> average 7.33 over 3/3 cases (35s)
        run 2: 7,   8, 7.5  -> average 7.50 over 3/3 cases (39s)

    TWO WRONG TURNS WORTH KEEPING
    1. Using claude-opus-5 as the model under test instead of Haiku. Adaptive
       thinking consumed the whole max_tokens budget: one case returned
       stop_reason=max_tokens with 0 characters after 47 seconds, and the
       grader then INVENTED a 5/10 review of the empty string. The broken
       average (7.17) was HIGHER than the honest one (5.33) — an eval that
       flatters itself is worse than no eval.
    2. Grading via prefill + stop_sequences. The grader quotes the solution,
       and a regex solution contains sequences like backslash-d, which must be
       DOUBLE-escaped inside a JSON string. When the grader got that wrong,
       json.loads() raised "Invalid escape" and the case was lost. It happened
       on the regex task in two consecutive runs but would not reproduce on
       demand — it depends on what the grader chooses to quote. Switching the
       grader to output_config.format removes the class of failure entirely,
       because the API constrains generation to the schema and the reply is
       well-formed JSON by construction.
       Dataset generation (exercise 10) keeps prefill: task descriptions
       contain no backslashes, so it has nothing to get wrong.

    A THIRD THING THE SCORES TAUGHT
    A case the pipeline could not grade must not be scored 0. Doing so blames
    the prompt for our own bug — one such case pulled the average from 7.33 to
    3.67. run_eval() now excludes ungraded cases, reports the average as
    "over N/M cases", and warns separately. A metric must always say what it
    is an average OF.

    Expect ~40s for 3 cases on Haiku. Progress prints per case so a long wait
    is visibly work rather than a hang.
"""

import json
import time
from pathlib import Path
from statistics import mean

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-haiku-4-5"             # the model under evaluation (as the course does)
GRADER_MODEL = "claude-haiku-4-5"      # judges the output; accepts prefill

DATASET_PATH = Path(__file__).parent / "dataset.json"


def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})


def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})


def chat(messages, system=None, model=MODEL, stop_sequences=None, max_tokens=4000,
         output_schema=None):
    # 4000, not 2000: with thinking on, a 2000 budget was consumed entirely by
    # reasoning on one task and returned ZERO text. See the note at the foot.
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
    """Merges the prompt and test case input, then returns the result."""
    prompt = f"""
Please solve the following task:

{test_case["task"]}
"""
    messages = []
    add_user_message(messages, prompt)
    return chat(messages)          # the MESSAGE — the caller needs stop_reason


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
    """Feeds the task and the output to a second model for judgement.

    Note the .format() — the lesson omits it, and without it the grader sees
    literal "{task}" and "{solution}" and scores everything 0."""
    messages = []
    add_user_message(messages, EVAL_PROMPT.format(task=test_case["task"], solution=output))

    # A SCHEMA, not prefill + stop_sequences. The lesson uses prefill, and for
    # dataset generation that is fine — task descriptions contain no
    # backslashes. Grading is different: the grader quotes the solution, and a
    # regex solution contains sequences like backslash-d, which must appear
    # inside a JSON string as a DOUBLE backslash. When the grader gets that
    # wrong json.loads() raises "Invalid escape" and the case is lost.
    # Observed twice in two consecutive runs on regex tasks, though not
    # reproducible on demand — it depends on what the grader chooses to quote.
    # output_config.format removes the class of failure: the API constrains
    # generation to the schema, so the reply is well-formed JSON by
    # construction. Prefill guarantees nothing about well-formedness.
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
    output = text_of(message)
    print(f"{label}  solved in {time.perf_counter() - started:4.1f}s "
          f"(stop={message.stop_reason}, {len(output)} chars)", flush=True)

    # Never grade a turn that did not finish. A truncated or empty output is a
    # pipeline failure, not a quality signal — and a model grader will happily
    # invent a review of an empty string, which is how a 0-char output scored
    # 5/10 before this guard existed.
    if message.stop_reason != "end_turn" or not output.strip():
        print(f"{label}  NOT GRADED (score=None)", flush=True)
        return {
            "output": output,
            "test_case": test_case,
            "score": None,
            "reasoning": f"NOT GRADED — stop_reason={message.stop_reason}, "
                         f"{len(output)} chars of text",
            "strengths": [],
            "weaknesses": ["incomplete turn; raise max_tokens or retry"],
        }

    started = time.perf_counter()
    model_grade = grade_by_model(test_case, output)
    print(f"{label}  graded in {time.perf_counter() - started:4.1f}s "
          f"-> {model_grade['score']}/10", flush=True)

    return {
        "output": output,
        "test_case": test_case,
        "score": model_grade["score"],
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

    # A case the pipeline failed to grade is NOT a zero. Scoring it 0 blames the
    # prompt for our own bug and drags the average down; scoring it 10 would
    # flatter it. Exclude it and report the exclusion, so the number always says
    # what it is an average OF.
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
    print(f"\n--- score {score}")
    print(f"task:       {result['test_case']['task'][:90]}")
    print(f"output len: {len(result['output'])} chars")
    print(f"reasoning:  {result['reasoning'][:180]}")
    print(f"weaknesses: {result['weaknesses']}")

# NOTES FROM THE COURSE
# - A grader returns a usable signal, typically 1-10.
# - Ask for strengths, weaknesses and reasoning as well as the score. Without
#   them models default to a middling ~6 and the metric stops discriminating.
# - Model graders suit judgements that are hard to express in code: task
#   following, completeness, helpfulness, safety. Code graders suit format and
#   syntax, which is the next section.
# - Model graders are "somewhat capricious" but give a consistent baseline.
#
# WORTH KNOWING (Domain 4)
# - Asking for reasoning BEFORE the score is the point, not decoration: it
#   forces the judgement to be derived rather than guessed. Same principle as
#   explicit criteria in D4.1.
# - The grader is a prompt too, and nothing here evaluates IT. A capricious
#   grader silently moves every score. That is the limit of model grading and
#   the reason code graders exist for anything mechanically checkable.
# - Keeping strengths/weaknesses in the result, not just the number, is what
#   makes a low score actionable rather than merely alarming.
#
# FOUND WHILE RUNNING THIS, 1 Sep 2026 — a three-link failure chain
#   With max_tokens=2000 and thinking on by default, one task came back:
#       stop_reason: max_tokens   blocks: ['thinking']
#       output_tokens: 2000 (all thinking)   text length: 0
#   The pipeline then:
#     1. did not check stop_reason
#     2. passed an empty string to the grader
#     3. and the grader INVENTED a detailed 5/10 review of the absent solution
#     4. which was averaged in as a real score
#   Three lessons, one bug:
#     D1.1  max_tokens is NOT "done". Check stop_reason before using content.
#     D5.3  the failure lost its failure-ness crossing into the grader.
#     D4    a model grader will confabulate. It cannot tell you that its input
#           was missing — it will score it anyway, plausibly.
#   Fixed by raising max_tokens AND refusing to grade a turn that did not end
#   with end_turn. The guard matters more than the budget: a bigger budget just
#   makes the same bug rarer. Note that even max_tokens=4000 still returns 0
#   chars of text on one task in this dataset — thinking eats the lot.
#
# SECOND FRAGILITY, same run
#   The grader stops at "```", and every solution it grades CONTAINS code
#   fences. When the grader echoes one inside its JSON, the stop fires
#   mid-payload and json.loads() raises, killing the whole eval run. Observed
#   once, not reproduced on the next run — so it is intermittent, which is
#   worse than deterministic: it will appear in CI and not on your machine.
#   grade_by_model() now returns an unparseable-marker result instead of
#   raising. A json_schema grader (exercise 08) does not have this failure mode
#   at all, but needs a model that permits no prefill.
