"""
Exercise 17 — structure with XML tags.

Course C, section: "Structure with XML tags" (prompt-engineering block,
technique 2).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    (paste the section URL here)

WHAT THIS TEACHES
    XML tags mark where one kind of content ends and another begins, so the
    model never has to guess whether a line is instruction or data. Rules of
    thumb from the lesson:
      - invent DESCRIPTIVE tag names: <sales_records> beats <data>,
        <my_code> and <docs> beat an undifferentiated wall of text
      - most valuable when interpolating LARGE or MIXED content (code +
        docs, 20 pages of records, multiple variables)
      - for short simple prompts, expect little movement — the value grows
        with prompt complexity

    v3 = v2 (exercise 16) with the four interpolated inputs wrapped in
    <athlete_information> ... </athlete_information> and the instruction
    pointed at the tag. Content unchanged; only the boundaries are new.

THE EXPERIMENT — and why a null result would still be a result
    Same control, same extra_criteria; sole change is structure. Exercise
    16 measured the noise floor: an unchanged prompt moved 8.33 -> 7.67
    (~0.7) between runs. The lesson predicts small gains on a prompt this
    simple — so the honest expectation is a delta WITHIN the noise floor.
    Knowing a change is insurance for larger prompts rather than points on
    this eval is itself the D4 skill: not every good practice shows up on
    every metric, and a metric that did not move is not proof the practice
    is worthless — it is proof this test was not the one that stresses it.
    (The eval's own prompts have used XML tags since exercise 12 — <task>,
    <solution>, <criteria> — precisely because THOSE interpolate mixed
    content.)

EXAM LINK
    D4 — interpreting deltas against measured variance; a change smaller
    than run-to-run noise on the same prompt demonstrates nothing, in
    either direction.

RUN
    From the repo root. Requires dataset-meal-plan.json (exercise 15).
        .venv/bin/python academy/course-c-claude-api/exercises/17-structure-with-xml-tags.py

    MEASURED 1 Sep 2026, claude-haiku-4-5, same control:
        9, 9, 9  -> average 9.00 over 3 cases (14s)
        v2 (exercise 16): 8.33 and 7.67 over two runs, noise ~0.7

    Read this the disciplined way: +0.67 against v2's better run is AT the
    noise floor, so one run of three cases cannot claim the mean moved —
    exactly the modest result the lesson predicts for a prompt this simple.
    The suggestive part is the spread: 9/9/9 is the first zero-spread run
    of the block (v2's runs: 7-9 and 6-9). Consistent with tags helping
    consistency rather than peak quality — but proving that would take
    repeated runs, not one lucky triple.
"""

import sys
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
JSON_OUT = HERE / "17-output.json"
HTML_OUT = HERE / "17-report.html"

if not DATASET_PATH.exists():
    sys.exit("dataset-meal-plan.json missing — run exercise 15 first; the "
             "comparison to the block's scores needs the SAME dataset")

evaluator = PromptEvaluator(max_concurrent_tasks=3)


# ------------------------------------------------------ the v3 prompt
def run_prompt(prompt_inputs):
    """v2 (exercise 16) with the interpolated data fenced in a descriptive
    tag. The ONLY change in this iteration is structure."""
    prompt = f"""
<athlete_information>
- Height: {prompt_inputs["height"]}
- Weight: {prompt_inputs["weight"]}
- Goal: {prompt_inputs["goal"]}
- Dietary restrictions: {prompt_inputs["restrictions"]}
</athlete_information>

Generate a meal plan based on the athlete information above.

Guidelines:
1. Include accurate daily calorie amount
2. Show protein, fat, and carb amounts
3. Specify when to eat each meal
4. Use only foods that fit restrictions
5. List all portion sizes in grams
6. Keep budget-friendly if mentioned
"""
    messages = []
    add_user_message(messages, prompt)
    return text_of(chat(messages))


# ------------------------------------------------------ the evaluation
print("evaluating the v3 prompt (XML structure — sole change vs 16)...", flush=True)
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
print(f"\nv2 (exercise 16): 8.33 / 7.67 over two runs, noise ~0.7  |  report: {HTML_OUT}")
for result in results:
    print(f"\n--- score {result['score']}/10")
    print(f"scenario:  {result['test_case']['scenario'][:90]}")
    print(f"reasoning: {result['reasoning'][:180]}")

# NOTES FROM THE COURSE
# - Tags are delimiters, not magic: they answer "which pieces of text belong
#   together and what does each section represent".
# - Any tag name is legal; pick descriptive ones. <sales_records> not
#   <data>; <my_code> vs <docs> for the debug-with-documentation case.
# - Highest value: large interpolated context, mixed content types, complex
#   multi-variable prompts. Simple prompts may show little improvement —
#   the lesson says so explicitly.
#
# WORTH KNOWING (Domain 4 / production habit)
# - The technique's real payoff is INJECTION RESISTANCE and parseability at
#   scale: when user-supplied data lands inside a clearly-fenced region,
#   instructions hiding in the data are easier for the model to treat as
#   data. That property does not show on this eval at all — another case of
#   a real benefit invisible to the current metric.
# - This repo has been using the technique on the EVAL side since exercise
#   12 (<task>/<solution>/<criteria>), where the interpolated content is
#   genuinely mixed — quoted solutions containing code fences and regexes.
