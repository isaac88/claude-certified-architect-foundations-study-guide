"""
Exercise 16 — being specific.

Course C, section: "Being specific" (prompt-engineering block, technique 1).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    (paste the section URL here)

WHAT THIS TEACHES
    The first and cheapest technique: tell the model exactly what the output
    must contain instead of leaving it to interpretation. Two kinds of
    specificity, often combined:
      output quality guidelines   length, structure, required elements, tone
                                  -> use in ALMOST EVERY prompt
      process steps               "brainstorm -> pick -> outline" sequences
                                  -> for complex/multi-angle problems only
    This lesson's meal-plan prompt needs the first kind: v2 is the naive
    prompt from exercise 15 plus six output guidelines, changing NOTHING
    else. The lesson's own measurement: 3.92 -> 7.86.

THE EXPERIMENT — one change, everything else held
    Same dataset (dataset-meal-plan.json, the block's control), same
    extra_criteria, same evaluator, same model. The only edited artefact is
    the prompt string. Whatever the score does, specificity did it.

    Note how the guidelines line up with the mandatory extra_criteria from
    exercise 15 (calories, macros, timing): being specific works here
    because the prompt now SAYS what the rubric CHECKS. A prompt cannot
    reliably satisfy criteria it was never told about — that was the whole
    failure of the naive version, and it is a requirements problem, not an
    intelligence problem.

EXAM LINK
    D4 — explicit, testable criteria, now on the GENERATION side: exercise
    05 put them in a system prompt, 14 put them in the judge, this file
    puts them in the task prompt. Same principle at all three stations.
    Also the iterate rule: one technique per iteration, delta vs 15's 4.67.

RUN
    From the repo root. Requires dataset-meal-plan.json (exercise 15).
        .venv/bin/python academy/course-c-claude-api/exercises/16-being-specific.py

    MEASURED 1 Sep 2026, claude-haiku-4-5, same control as exercise 15:
        9, 7, 9  -> average 8.33 over 3 cases (12s)
        baseline (15, naive prompt): 2, 5, 7 -> 4.67

    Both things moved, and the second matters more:
        mean    4.67 -> 8.33   (the lesson's own jump was 3.92 -> 7.86)
        spread  2-7  -> 7-9    (worst case +7, best case +2)
    The case that scored 2 at baseline — the vegan rock climber, where the
    naive prompt ignored the mandatory format entirely — scored 9 here.
    Guidelines helped the WORST case most: specificity buys reliability
    first, quality second.
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
JSON_OUT = HERE / "16-output.json"
HTML_OUT = HERE / "16-report.html"

if not DATASET_PATH.exists():
    sys.exit("dataset-meal-plan.json missing — run exercise 15 first; the "
             "comparison to its baseline needs the SAME dataset")

evaluator = PromptEvaluator(max_concurrent_tasks=3)


# ------------------------------------------------------ the v2 prompt
def run_prompt(prompt_inputs):
    """v1 (exercise 15) plus the lesson's six output guidelines. The ONLY
    change in this iteration."""
    prompt = f"""
What should this person eat?

- Height: {prompt_inputs["height"]}
- Weight: {prompt_inputs["weight"]}
- Goal: {prompt_inputs["goal"]}
- Dietary restrictions: {prompt_inputs["restrictions"]}

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
print("evaluating the v2 prompt (guidelines added — sole change vs 15)...", flush=True)
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
print(f"\nbaseline (exercise 15): 4.67  |  report: {HTML_OUT}")
for result in results:
    print(f"\n--- score {result['score']}/10")
    print(f"scenario:  {result['test_case']['scenario'][:90]}")
    print(f"reasoning: {result['reasoning'][:180]}")

# NOTES FROM THE COURSE
# - Two kinds of specificity: output quality guidelines (use nearly always)
#   and process steps (for troubleshooting, decisions, critical thinking —
#   anywhere the model should consider multiple angles before answering).
# - The course's measured jump on this exact change: 3.92 -> 7.86.
# - Guidelines constrain the countless-directions problem: length, cast
#   size, scenario shape for a story; calories, macros, grams for a meal.
# - Combine both kinds in professional prompts: guidelines for consistency
#   of output, steps for coverage of thinking.
#
# WORTH KNOWING (Domain 4)
# - The guidelines mirror the eval's mandatory criteria almost line for
#   line. That is legitimate, not cheating: the criteria ARE the product
#   requirements, and the prompt is the spec handed to the model. Prompt
#   and rubric drifting apart is how "the model is bad at this" gets said
#   about a model that was never told the requirements.
# - Corollary worth remembering for production: when the rubric changes,
#   the prompt must change with it — they are two copies of one contract.
