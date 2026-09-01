"""
Exercise 18 — providing examples (one-shot / multi-shot).

Course C, section: "Providing examples" (prompt-engineering block,
technique 3).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287746

WHAT THIS TEACHES
    Show, don't tell. A sample input/output pair communicates requirements
    that are hard to phrase as instructions — the lesson's case is sarcasm
    in sentiment analysis: "best movie since Plan 9" LOOKS positive, and no
    guideline says otherwise as effectively as one sarcastic example
    labelled Negative. One-shot = a single pair to set the pattern;
    multi-shot = several pairs to cover different edge cases.

    Where do good examples come from? YOUR OWN EVAL RESULTS: take a
    top-scoring output and freeze it into the prompt as the ideal, wrapped
    in <sample_input>/<ideal_output> tags, plus a sentence saying WHY it is
    good (the lesson: format alone is not the message — the reasoning is).

    v4 = v3 (exercise 17) + one frozen example: the 9/10 rock-climber plan
    from 17-output.json. Sole change of the iteration.

TWO HONEST PROBLEMS WITH THIS ITERATION, both worth knowing
    1. CONTAMINATION. The example IS one of the control's three test cases.
       For the rock-climber case the prompt now contains a near-answer, so
       that case's score no longer measures generalisation — it measures
       copying. Real evals hold examples OUT of the test set; the lesson's
       "mine your eval for examples" needs that caveat. Noted per-case in
       the measured results below.
    2. CEILING. v3 already scored 9.00, so this metric has almost no room
       to show the technique's value. Examples earn their keep on corner
       cases (sarcasm, ambiguous inputs, exact formats) — a rubric this
       mechanical, already satisfied, cannot surface that. A null result
       here says nothing against the technique (same lesson as 17).

    Also visible in the frozen example: its daily totals (2,700 kcal) sit
    OUTSIDE its own stated target (2,400-2,600) — our "ideal" carries a
    real arithmetic inconsistency. One-shot teaches the flaw along with the
    format; the example you show is a spec you cannot contradict.

EXAM LINK
    D4 — example selection is eval design: train/test separation (the
    contamination above), ceiling effects, and the cost side — this one
    example roughly triples the prompt's input tokens ON EVERY CALL.
    Examples are a per-request tax that must pay for itself in quality.

RUN
    From the repo root. Requires dataset-meal-plan.json (exercise 15).
        .venv/bin/python academy/course-c-claude-api/exercises/18-providing-examples.py

    MEASURED 1 Sep 2026, claude-haiku-4-5, same control:
        run 1: 8 (rock climber, CONTAMINATED), 9, 8  -> average 8.33 (17s)
        run 2: 9 (contaminated), 9, 7           -> average 8.33 (committed)
        v3 (exercise 17): 9.00 and 8.00 over two runs; noise ~0.7
    Two runs, same mean, shuffled per-case scores — the per-case numbers
    are noisier than the average. v4 == v3 within noise either way.

    -0.67 vs v3 — within the noise floor, so the run shows NO measurable
    change, exactly what ceiling + a mechanical rubric predicts. The detail
    worth keeping: the contaminated case scored 8 — LOWER than the 9 it
    scored without its own near-answer in the prompt. Even contamination
    could not push through the ceiling; and an in-prompt ideal does not
    guarantee its own case a 10, because the grader still judges the
    output, not the resemblance. Net position for v4: same score band as
    v3 at roughly 3x the input tokens per request — on THIS task the
    example does not pay for itself; on a corner-case-rich task (sarcasm)
    it would. Technique cost-effectiveness is task-dependent, and only an
    eval tells you which side you are on.
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
JSON_OUT = HERE / "18-output.json"
HTML_OUT = HERE / "18-report.html"

if not DATASET_PATH.exists():
    sys.exit("dataset-meal-plan.json missing — run exercise 15 first; the "
             "comparison to the block's scores needs the SAME dataset")

evaluator = PromptEvaluator(max_concurrent_tasks=3)


# ------------------------------------------------ the frozen example
# The highest-scoring output of exercise 17 (score 9, rock-climber case),
# copied VERBATIM from 17-output.json and frozen here. Frozen, not loaded
# at runtime: if this file read 17-output.json, regenerating that file
# would silently change this prompt — and a prompt version must not change
# between the runs that measure it.
EXAMPLE_INPUT = """\
- Height: 168
- Weight: 58
- Goal: High-performance rock climbing with sustained energy and strength
- Dietary restrictions: Vegetarian, nut allergy"""

EXAMPLE_OUTPUT = """\
# Rock Climbing Nutrition Plan
## Athlete Profile: 168cm, 58kg, Vegetarian, Nut Allergy

---

## Daily Calorie & Macro Target
- **Daily Calories:** 2,400-2,600 kcal
- **Protein:** 100-110g (17%)
- **Carbohydrates:** 310-330g (52%)
- **Fat:** 65-75g (25-27%)

*Rationale: High carbs for sustained climbing energy; adequate protein for muscle recovery; moderate fat for hormone health*

---

## Daily Meal Plan

### BREAKFAST (7:00 AM) — 550 kcal
**Oatmeal Power Bowl**
- Rolled oats: 60g
- Banana: 120g
- Greek yogurt (plain, non-fat): 150g
- Sunflower seed butter: 20g
- Honey: 15g
- Cinnamon: 2g

| Macro | Amount |
|-------|--------|
| Protein | 18g |
| Carbs | 72g |
| Fat | 10g |

---

### MID-MORNING SNACK (10:00 AM) — 280 kcal
**Smoothie**
- Plain plant-based milk (soy/oat): 250ml
- Whey or pea protein powder: 30g
- Blueberries (frozen): 80g
- Banana: 80g
- Flax seeds: 10g

| Macro | Amount |
|-------|--------|
| Protein | 26g |
| Carbs | 32g |
| Fat | 6g |

---

### LUNCH (12:30 PM) — 650 kcal
**Lentil & Quinoa Bowl**
- Cooked quinoa: 100g
- Cooked red lentils: 150g
- Roasted chickpeas: 50g
- Roasted sweet potato: 150g
- Spinach (raw): 50g
- Olive oil (dressing): 10ml
- Lemon juice & garlic: to taste

| Macro | Amount |
|-------|--------|
| Protein | 22g |
| Carbs | 78g |
| Fat | 12g |

---

### PRE-CLIMB SNACK (2.5 hours before climbing) — 320 kcal
**Energy & Recovery Combo**
- Whole grain bread: 80g (2 slices)
- Hummus: 40g
- Cucumber: 100g
- Banana: 100g
- Dried apricots: 40g

| Macro | Amount |
|-------|--------|
| Protein | 12g |
| Carbs | 56g |
| Fat | 6g |

---

### DINNER (7:00 PM) — 650 kcal
**Vegetarian Stir-Fry**
- Firm tofu (cubed, pressed): 200g
- Brown rice: 80g (cooked)
- Broccoli: 120g
- Carrots: 80g
- Bell pepper: 100g
- Sesame oil: 10ml
- Low-sodium soy sauce: 10ml

| Macro | Amount |
|-------|--------|
| Protein | 22g |
| Carbs | 70g |
| Fat | 18g |

---

### POST-CLIMB RECOVERY (if climbing in evening) — 250 kcal
*Skip if consuming dinner within 1 hour of climbing*
- Greek yogurt: 150g
- Granola (nut-free): 30g
- Honey: 10g
- Berries: 60g

| Macro | Amount |
|-------|--------|
| Protein | 15g |
| Carbs | 32g |
| Fat | 3g |

---

## Daily Totals
| Nutrient | Amount |
|----------|--------|
| **Calories** | 2,700 |
| **Protein** | 115g |
| **Carbohydrates** | 340g |
| **Fat** | 65g |

---

## Key Nutrition Tips for Climbing

✓ **Hydration:** 3-4 liters water daily; add electrolytes during intense sessions
✓ **Timing:** Eat main meals 3-4 hours before climbing; snacks 1-2 hours before
✓ **Recovery:** Carb + protein within 30-60 minutes post-climb
✓ **Iron:** Include lentils, tofu, pumpkin seeds (vegetarian protein + iron source)
✓ **Calcium:** Greek yogurt, fortified plant milk, leafy greens

---

## Budget-Friendly Staples
- Dried lentils & chickpeas
- Oats & brown rice
- Frozen vegetables
- Seasonal fruit (bananas, apples)
- Tofu & plant-based yogurt
- Seeds (sunflower, flax, pumpkin)"""


# ------------------------------------------------------ the v4 prompt
def run_prompt(prompt_inputs):
    """v3 (exercise 17) plus one frozen example — the ONLY change."""
    prompt = f"""
Here is an example of an athlete information input with an ideal response:

<sample_input>
{EXAMPLE_INPUT}
</sample_input>
<ideal_output>
{EXAMPLE_OUTPUT}
</ideal_output>

This example is well-structured, provides exact foods, portion sizes in
grams and meal timing, and aligns with the athlete's goals and dietary
restrictions.

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
print("evaluating the v4 prompt (one-shot example — sole change vs 17)...", flush=True)
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
print(f"\nv3 (exercise 17): 9.00  |  noise ~0.7  |  report: {HTML_OUT}")
for result in results:
    contaminated = "rock climber" in result["test_case"]["scenario"].lower()
    tag = "  [CONTAMINATED — example is this case's near-answer]" if contaminated else ""
    print(f"\n--- score {result['score']}/10{tag}")
    print(f"scenario:  {result['test_case']['scenario'][:90]}")
    print(f"reasoning: {result['reasoning'][:180]}")

# NOTES FROM THE COURSE
# - One-shot sets the pattern; multi-shot covers edge cases. Reach for
#   examples when instructions get long or subtle: corner cases, exact
#   output formats, tone, ambiguous inputs.
# - Mine evaluation results for the highest-scoring outputs and promote
#   them to in-prompt examples.
# - Wrap in XML (<sample_input>/<ideal_output>), announce them explicitly
#   ("Here is an example... with an ideal response"), and SAY WHY the
#   example is ideal — the reasoning is part of the teaching signal.
# - Choose examples that address your most common failure cases.
#
# WORTH KNOWING (Domain 4)
# - Train/test separation applies to prompts, not just ML: an example
#   promoted from the eval set contaminates that case forever after.
#   Production shape: keep an example pool disjoint from the eval set.
# - Examples are the most expensive technique so far: this one adds ~1,200
#   tokens to EVERY request. Guidelines cost ~60. When two techniques
#   reach the same score, the cheaper prompt wins — input tokens are a
#   unit economic, not a rounding error (D2/D5 crossover).
# - The example's own arithmetic flaw (totals outside its stated target)
#   ships with it. Vet an example harder than any instruction, because the
#   model will copy what it does, not what it meant to do.
