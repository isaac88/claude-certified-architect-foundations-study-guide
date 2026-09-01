"""
Exercise 15 — prompt engineering: the baseline.

Course C, section: "Prompt engineering" (first lesson of the block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287744
    Scaffolding from the official 001_prompting.ipynb, adapted in
    prompt_evaluator.py (adaptations documented there).

WHAT THIS TEACHES
    The iterative cycle the whole block hangs off: set a goal -> write an
    initial prompt -> evaluate -> apply ONE technique -> re-evaluate, and
    repeat the last two until satisfied. This lesson does the first three
    steps: a deliberately naive prompt ("What should this person eat?")
    against a generated dataset, to establish a numeric BASELINE. The lesson
    says a first score around 2.3/10 is typical — low is expected; the
    number exists to measure improvement against, not to be good.

    New machinery over exercises 10-14 (all in prompt_evaluator.py):
      - PromptEvaluator(max_concurrent_tasks=3) — threaded generation and
        grading; the lesson says start low to dodge rate limits
      - generate_dataset(task_description, prompt_inputs_spec, ...) — test
        cases are now STRUCTURED INPUTS (height/weight/goal/restrictions)
        plus solution_criteria, not a single task string
      - run_evaluation(run_prompt_function, dataset_file, extra_criteria)
        — extra_criteria are MANDATORY requirements: any violation caps the
        score at 3. That is what makes the naive prompt score ~2-3 rather
        than a polite ~6: the rubric has teeth
      - an HTML report beside the JSON, for reading per-case reasoning

DATASET — this block has its own control
    Files are prefixed to keep them apart from the exercise 10-14 pipeline:
        dataset-meal-plan.json   the control for the WHOLE block
        15-output.json / 15-report.html   this exercise's results
    The dataset is generated ONCE (only if the file is missing) and then
    reused by every technique lesson — exercise 10's rule: if the inputs
    change between runs, a score change tells you nothing.

EXAM LINK
    D4 — the baseline habit: no prompt change without a number to compare
    against, and one change at a time so the delta is attributable. Also
    "how would you know this got worse?" — after this file, the answer is
    "re-run the eval and compare to 15's number".

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/15-prompt-engineering.py

    MEASURED 1 Sep 2026, claude-haiku-4-5, first run — THE BLOCK'S BASELINE:
        2, 5, 7  -> average 4.67 over 3 cases (10s, dataset generation ~9s more)

    Higher than the lesson's "typical 2.3" — today's Haiku is simply
    stronger than the model the course recorded against. The number that
    matters more is the SPREAD: the same naive prompt scored 2 on one case
    (ignored the mandatory format entirely) and 7 on another. An unreliable
    prompt does not average out — it fails some users completely. Reducing
    that spread, not just raising the mean, is what the block's techniques
    are for.
"""

import json
import time
from pathlib import Path

from prompt_evaluator import (
    PromptEvaluator,
    add_user_message,
    chat,
    text_of,
)

HERE = Path(__file__).parent
DATASET_PATH = HERE / "dataset-meal-plan.json"
JSON_OUT = HERE / "15-output.json"
HTML_OUT = HERE / "15-report.html"

evaluator = PromptEvaluator(max_concurrent_tasks=3)

# ---------------------------------------------------- step 1: the dataset
# Generated once and kept: the control for the whole prompt-engineering
# block. Delete the file deliberately if you ever want a fresh control —
# and accept that every earlier score is retired with it.
if DATASET_PATH.exists():
    dataset = json.loads(DATASET_PATH.read_text())
    print(f"using existing {DATASET_PATH.name} ({len(dataset)} cases) — the control stands")
else:
    print("generating dataset (once — it becomes the block's control)...", flush=True)
    dataset = evaluator.generate_dataset(
        task_description="Write a compact, concise 1 day meal plan for a single athlete",
        prompt_inputs_spec={
            "height": "Athlete's height in cm",
            "weight": "Athlete's weight in kg",
            "goal": "Goal of the athlete",
            "restrictions": "Dietary restrictions of the athlete",
        },
        output_file=str(DATASET_PATH),
        num_cases=3,
    )
    print(f"wrote {DATASET_PATH.name} with {len(dataset)} cases")


# ------------------------------------------- step 2: the naive v1 prompt
def run_prompt(prompt_inputs):
    """Deliberately basic — the point is a measurable starting line."""
    prompt = f"""
What should this person eat?

- Height: {prompt_inputs["height"]}
- Weight: {prompt_inputs["weight"]}
- Goal: {prompt_inputs["goal"]}
- Dietary restrictions: {prompt_inputs["restrictions"]}
"""
    messages = []
    add_user_message(messages, prompt)
    return text_of(chat(messages))


# ------------------------------------------------- step 3: the evaluation
print("\nevaluating the naive prompt...", flush=True)
started = time.perf_counter()

results = evaluator.run_evaluation(
    run_prompt_function=run_prompt,
    dataset_file=str(DATASET_PATH),
    extra_criteria="""
The output should include:
- Daily caloric total
- Macronutrient breakdown
- Meals with exact foods, portions, and timing
""",
    json_output_file=str(JSON_OUT),
    html_output_file=str(HTML_OUT),
)

print(f"({time.perf_counter() - started:.0f}s)")
print(f"\nreport: {HTML_OUT}")
for result in results:
    print(f"\n--- score {result['score']}/10")
    print(f"scenario:  {result['test_case']['scenario'][:90]}")
    print(f"reasoning: {result['reasoning'][:180]}")

# NOTES FROM THE COURSE
# - The cycle: goal -> initial prompt -> evaluate -> apply a technique ->
#   re-evaluate. Repeat the last two. Each iteration should move the number.
# - Start max_concurrent_tasks low (~3); raise it if your rate limits allow.
# - Keep num_cases small (2-3) while iterating; grow it for final validation.
# - A first score of ~2.3/10 is typical and fine. The score is a ruler, not
#   a verdict.
# - extra_criteria = requirements that matter for YOUR use case, over and
#   above the per-case solution_criteria. Violating one is an automatic
#   fail (<= 3) — that is what gives the eval discrimination at the bottom
#   of the scale.
# - ONE change per iteration, or the delta tells you nothing about which
#   technique earned it.
#
# WORTH KNOWING (Domain 4)
# - This grader fixes exercise 12's "everything scores ~6" problem from the
#   other end: scoring BANDS tied to mandatory/secondary criteria, an order
#   to use the whole 1-10 scale, and "do not add your own requirements".
#   Rubric design is prompt engineering applied to the judge.
# - The concurrency is why the eval takes ~15s instead of ~45s: eval speed
#   is iteration speed, and iteration speed decides how many prompt
#   versions you actually try. That is an architectural property of the
#   eval, not a nicety (D5 sees the same tradeoff as request fan-out).
# - The naive prompt is not a straw man; it is the control arm. Without a
#   measured "before", any technique looks like it worked.
