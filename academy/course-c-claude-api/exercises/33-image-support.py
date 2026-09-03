"""
Exercise 33 — image support.

Course C, section: "Image support" (Features of Claude block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287778
    Code from the official 002_images.ipynb — a STARTER notebook: its last
    cell is literally "# TODO: Read image data, feed into Claude", so the
    fire-risk run below is that TODO completed.

WHAT THIS TEACHES
    An image is just another CONTENT BLOCK in a user message: {"type":
    "image", "source": {"type": "base64", "media_type": ..., "data": ...}}
    sitting next to the text block. The flow, history rules and response
    shape are unchanged from text-only chat — vision adds an input type,
    not a new API.

    Limits worth memorising: 100 images per request, 5MB each, 8000px
    max edge alone / 2000px when sending several, base64 or URL source,
    and cost ≈ (width × height) / 750 tokens per image.

    The lesson's real claim: PROMPTING TECHNIQUE TRANSFERS. A bare
    "give me a fire risk score" and a 5-step methodology prompt are the
    same image tokens — the structured one buys named evidence per step,
    a defined rating scale, and an auditable answer.

EXAM LINK
    D4 — specificity, step-by-step decomposition and one-shot examples
    apply to images exactly as to text; a rubric defined IN the prompt
    (the 1-4 rating table) is the graded-output lesson from the eval
    block, relocated into vision.

DIVERGENCES
    - Notebook's chat() still passes temperature=1.0 — removed in SDK
      1.2.0 (exercise 06 row); dropped here.
    - Notebook model: claude-sonnet-4-5 (second section off Haiku after
      exercises 24-26). Kept for fidelity.

RUN
    Needs the lesson's images.zip extracted to exercises/images/ (that
    folder is GITIGNORED — the props are Anthropic course assets and this
    repo is public; re-download from the lesson page if missing).

    From the repo root (three calls, ~1 minute):
        .venv/bin/python academy/course-c-claude-api/exercises/33-image-support.py

    MEASURED 3 Sep 2026, claude-sonnet-4-5:
        prop1 (928x1226): formula ~1516 tokens, measured input_tokens 1515
            -> the formula is essentially EXACT, and the 7-word question
               disappears into rounding — the image IS the bill.
        prop4 (1256x1790): formula says ~2997, but measured image cost was
            ~1560 tokens (simple call 1578 total; structured call 2059,
            and 2059 - 1578 = 481 = exactly the longer prompt text — the
            image portion was identical). The API DOWNSCALED it: images
            over ~1568px long edge / ~1600 tokens are resized server-side,
            so the formula is an upper bound for oversized images.
        simple vs structured, same image:
            simple     -> "Fire Risk Score: 2.5/4" — HALF-POINTS. No
                          rubric was given, so the model invented a finer
                          scale than the business defines; any downstream
                          int(rating) parse breaks.
            structured -> "Rating: 2 (Moderate Risk)", one sentence per
                          step, overhang placed in the prompt's own
                          <25% band. Same image tokens; the extra 481
                          prompt tokens bought a parseable contract and
                          auditable evidence, not just prettier prose.
"""

import base64
import struct
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-sonnet-4-5"          # the notebook's choice
IMAGES = Path(__file__).parent / "images"


# ---------------------------------------------------------------- helpers
def add_user_message(messages, message):
    content = message if isinstance(message, list) else [
        {"type": "text", "text": message}
    ]
    messages.append({"role": "user", "content": content})


def chat(messages, system=None):
    params = {"model": MODEL, "max_tokens": 4000, "messages": messages}
    if system:
        params["system"] = system
    return client.messages.create(**params)


def text_from_message(message):
    return "\n".join(b.text for b in message.content if b.type == "text")


def image_block(path):
    """The lesson's structure: read bytes -> base64 -> image content block."""
    with open(path, "rb") as f:
        image_bytes = base64.standard_b64encode(f.read()).decode("utf-8")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": image_bytes,
        },
    }


def png_dimensions(path):
    # Width/height live in the PNG IHDR chunk — no imaging library needed.
    with open(path, "rb") as f:
        header = f.read(24)
    return struct.unpack(">II", header[16:24])


def ask_about_image(path, prompt):
    messages = []
    add_user_message(messages, [image_block(path), {"type": "text", "text": prompt}])
    t0 = time.perf_counter()
    response = chat(messages)
    elapsed = time.perf_counter() - t0
    print(f"[{path.name}] input_tokens={response.usage.input_tokens} "
          f"output_tokens={response.usage.output_tokens} elapsed={elapsed:.1f}s")
    return response


# --------------------------- stage 1: the block structure + the token bill
print("=" * 70)
print("STAGE 1 — an image is a content block; its cost is (w x h) / 750")
print("=" * 70)
prop1 = IMAGES / "prop1.png"
w, h = png_dimensions(prop1)
estimate = w * h // 750
print(f"{prop1.name}: {w}x{h}px, size {prop1.stat().st_size // 1024}KB "
      f"-> formula estimate ~{estimate} image tokens")

response = ask_about_image(prop1, "What do you see in this image?")
print(f"-> formula {estimate} vs measured input_tokens "
      f"{response.usage.input_tokens} (difference = text prompt + overhead)")
print(f"\n{text_from_message(response)[:500]}")

# ------------------- stage 2: the lesson's claim — simple vs structured
# Same image, same image tokens. Only the words change.
FIRE_RISK_PROMPT = """
Analyze the attached satellite image of a property with these specific steps:

1. Residence identification: Locate the primary residence on the property by looking for:
   - The largest roofed structure
   - Typical residential features (driveway connection, regular geometry)
   - Distinction from other structures (garages, sheds, pools)
   Describe the residence's location relative to property boundaries and other features.

2. Tree overhang analysis: Examine all trees near the primary residence:
   - Identify any trees whose canopy extends directly over any portion of the roof
   - Estimate the percentage of roof covered by overhanging branches (0-25%, 25-50%, 50-75%, 75-100%)
   - Note particularly dense areas of overhang

3. Fire risk assessment: For any overhanging trees, evaluate:
   - Potential wildfire vulnerability (ember catch points, continuous fuel paths to structure)
   - Proximity to chimneys, vents, or other roof openings if visible
   - Areas where branches create a "bridge" between wildland vegetation and the structure

4. Defensible space identification: Assess the property's overall vegetative structure:
   - Identify if trees connect to form a continuous canopy over or near the home
   - Note any obvious fuel ladders (vegetation that can carry fire from ground to tree to roof)

5. Fire risk rating: Based on your analysis, assign a Fire Risk Rating from 1-4:
   - Rating 1 (Low Risk): No tree branches overhanging the roof, good defensible space around the structure
   - Rating 2 (Moderate Risk): Minimal overhang (<25% of roof), some separation between tree canopies
   - Rating 3 (High Risk): Significant overhang (25-50% of roof), connected tree canopies, multiple points of vulnerability
   - Rating 4 (Severe Risk): Extensive overhang (>50% of roof), dense vegetation against structure, numerous ember catch points, limited defensible space

For each item above (1-5), write one sentence summarizing your findings, with your final response being the numeric Fire Risk Rating (1-4) with a brief justification.
"""

print()
print("=" * 70)
print("STAGE 2 — same property: bare score request vs the 5-step methodology")
print("=" * 70)
prop4 = IMAGES / "prop4.png"

print("\n--- simple prompt ---")
simple = ask_about_image(prop4, "Provide a fire risk score from 1-4 for this property.")
print(text_from_message(simple))

print("\n--- structured 5-step prompt (the notebook's TODO, completed) ---")
structured = ask_about_image(prop4, FIRE_RISK_PROMPT)
print(text_from_message(structured))

# NOTES FROM THE COURSE
# - Limits: 100 images/request, 5MB/image, 8000px alone, 2000px when
#   several. Source is base64 or a URL. tokens = (w_px * h_px) / 750.
# - Order shown in the lesson: image block FIRST, text block after.
# - "How many marbles?" fails bare; a counting METHODOLOGY (identify one
#   at a time, then verify with a second pass in a stated order) and
#   one-shot examples (an image with a KNOWN count first) fix it. No
#   marble image ships in images.zip — the props are the worked example.
# - The fire-risk system replaces inspector visits with satellite imagery:
#   overhang %, ember paths, fuel ladders, defensible space -> 1-4 rating.
#
# WORTH KNOWING (D4/D5)
# - The rating table inside the prompt is the same move as the eval
#   block's solution_criteria (ex. 14): define the scale, or the model
#   invents one per call and scores drift.
# - Every image is re-billed on EVERY request that resends the history —
#   the multi-turn tax from ex. 04, at ~1.5-3k tokens per image per turn.
