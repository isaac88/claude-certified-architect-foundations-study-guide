"""
Exercise 06 — temperature.

Course C, section: "Temperature".
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287728

WHAT THIS TEACHES
    How Claude generates text: tokenize -> predict probabilities -> sample.
    Temperature reshapes that final sampling step. Near 0 it almost always
    takes the highest-probability token (predictable); near 1 it spreads
    probability across candidates (varied).

    Task ranges from the lesson:
      0.0-0.3  facts, code, extraction, moderation
      0.4-0.7  summarising, teaching, problem-solving
      0.8-1.0  brainstorming, creative writing, marketing, jokes

*** THE BIG DIVERGENCE ***
    `temperature` NO LONGER EXISTS on current models. Verified 31 Aug 2026:
      - anthropic SDK 1.2.0 has removed `temperature`, `top_p` and `top_k`
        from messages.create() entirely -> TypeError before any HTTP call.
      - The API itself answers: 400 "`temperature` is deprecated for this
        model." on claude-opus-5.
    The lesson's `chat(messages, system=None, temperature=1.0)` cannot run on
    any current model. Older dated snapshots still accept it, so stage 2 below
    demonstrates the concept there over raw HTTP.

EXAM LINK (Domain 1 + Domain 4)
    The scoring habit is "deterministic over probabilistic when stakes are
    high". Temperature 0 is NOT determinism — it biases sampling, it does not
    guarantee identical output (stage 2 shows this). Real determinism comes
    from code: validation, schemas, tool calls, programmatic enforcement.
    Answers that reach for temperature=0 to make something reliable are
    choosing a probabilistic knob for a deterministic requirement.

RUN
    From the repo root:
        .venv/bin/python academy/course-c-claude-api/exercises/06-temperature.py
"""

import json
import os
import urllib.error
import urllib.request

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()
MODEL = "claude-opus-5"
LEGACY_MODEL = "claude-sonnet-4-5-20250929"   # still accepts sampling params

PROMPT = "Give me one movie idea in one sentence."


# ---------------------------------------------------------------- the lesson's function
def chat(messages, system=None, temperature=1.0):
    """The lesson's version, verbatim in shape. It cannot work on a current
    model: the SDK no longer defines `temperature`."""
    params = {
        "model": MODEL,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
    }

    if system:
        params["system"] = system

    message = client.messages.create(**params)
    return message.content[0].text


# ---------------------------------------------------------------- stage 1
print("=" * 70)
print("STAGE 1 — the lesson's code against a current model")
print("=" * 70)

try:
    chat([{"role": "user", "content": PROMPT}], temperature=0.0)
    print("no error raised")
except TypeError as exc:
    print(f"TypeError: {exc}")
    print("-> The SDK dropped the parameter. This fails before any request.")

print()
print("Sampling parameters in SDK 1.2.0's messages.create():")
import inspect
sig = inspect.signature(client.messages.create)
for name in ("temperature", "top_p", "top_k"):
    print(f"  {name:12} {'present' if name in sig.parameters else 'REMOVED'}")
print()

print("And if we bypass the SDK and send it raw to a current model:")


def raw_call(model, temperature=None):
    payload = {"model": model, "max_tokens": 100,
               "messages": [{"role": "user", "content": PROMPT}]}
    if temperature is not None:
        payload["temperature"] = temperature
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(payload).encode(),
        headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
    )
    try:
        d = json.loads(urllib.request.urlopen(req).read())
        return None, "".join(b.get("text", "") for b in d["content"] if b["type"] == "text")
    except urllib.error.HTTPError as exc:
        return f"HTTP {exc.code}", json.loads(exc.read())["error"]["message"]


err, msg = raw_call(MODEL, temperature=0.0)
print(f"  {err}: {msg}" if err else f"  accepted: {msg[:80]}")
print()


# ---------------------------------------------------------------- stage 2
print("=" * 70)
print(f"STAGE 2 — the concept, demonstrated on {LEGACY_MODEL}")
print("=" * 70)
print("(a dated snapshot that still accepts sampling parameters)")
print()

for temp in (0.0, 1.0):
    print(f"--- temperature={temp}, three runs of the same prompt ---")
    seen = []
    for i in range(3):
        err, out = raw_call(LEGACY_MODEL, temperature=temp)
        if err:
            print(f"  run {i+1}: {err}: {out[:80]}")
            continue
        out = out.strip().replace("\n", " ")
        seen.append(out)
        print(f"  run {i+1}: {out[:95]}")
    if seen:
        print(f"  -> {len(set(seen))} distinct answer(s) out of {len(seen)}")
    print()

print("Read the temperature=0.0 block again. Identical or near-identical")
print("answers are LIKELY, not guaranteed. Temperature 0 biases sampling")
print("towards the top token; it is not a determinism switch.")
print()


# ---------------------------------------------------------------- stage 3
print("=" * 70)
print("STAGE 3 — what current models use instead")
print("=" * 70)

print("There is no drop-in replacement for temperature, because the newer")
print("models are tuned not to need one. The equivalent lever is effort,")
print("which controls reasoning depth and token spend:")
print()

for effort in ("low", "high"):
    r = client.messages.create(
        model=MODEL, max_tokens=1000,
        output_config={"effort": effort},
        messages=[{"role": "user", "content": PROMPT}],
    )
    text = "".join(b.text for b in r.content if b.type == "text").strip().replace("\n", " ")
    thinking = getattr(r.usage, "output_tokens_details", None)
    tk = getattr(thinking, "thinking_tokens", "n/a") if thinking else "n/a"
    print(f"  effort={effort:5} out={r.usage.output_tokens:4} thinking={tk:>4}  {text[:70]}")

print()
print("Effort is not a creativity dial — it trades thoroughness against cost.")
print("For output SHAPE, constrain it: structured outputs, or explicit criteria")
print("in the prompt. Those are deterministic; temperature never was.")

# NOTES FROM THE COURSE
# - Generation is tokenize -> predict probabilities -> sample. Temperature only
#   touches the sampling step.
# - The lesson's own caveat is important and cuts both ways: temperature does
#   not GUARANTEE different outputs at high values, and it does not guarantee
#   identical outputs at 0 either.
#
# DIVERGENCES, verified 31 Aug 2026
# 1. `temperature`, `top_p` and `top_k` are REMOVED from anthropic SDK 1.2.0's
#    messages.create() -> TypeError, no request sent.
# 2. The API returns 400 "`temperature` is deprecated for this model." for
#    claude-opus-5. Dated snapshots (e.g. claude-sonnet-4-5-20250929) still
#    accept it, which is the only way to demonstrate the lesson today.
# 3. `chat()` returning `message.content[0].text` — the same unsafe indexing
#    seen since exercise 02.
