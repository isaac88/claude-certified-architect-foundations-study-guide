"""
Exercise 34 — PDF support.

Course C, section: "PDF support" (Features of Claude block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287768

WHAT THIS TEACHES
    A PDF is the image lesson with four renames: read bytes -> base64 as
    before, then "type": "document" (not "image"), "media_type":
    "application/pdf" (not "image/png"). Same message flow, same history
    rules, same response shape. Claude reads the WHOLE document — body
    text, embedded images and charts, tables, structure — so extraction
    questions need no OCR pipeline in front.

EXAM LINK
    D5 — cost shape: a PDF page is billed roughly like text PLUS a
    rendered image of the page, so document workloads are priced per page,
    not per file. D2 — a checkable extraction (a named figure from an
    infobox) beats "summarise" for verifying the document actually parsed.

DIVERGENCES
    - None in the lesson's code itself. Same block model as exercise 33:
      claude-sonnet-4-5, chat() without temperature (SDK 1.2.0).
    - Current-API note: base64 is fine to 32MB/600 pages (100 pages on
      200k-context models); repeated use of the same document should move
      to the Files API ({"type": "file", "file_id": ...}) — later lesson.

RUN
    Needs the lesson's earth.pdf next to this file (GITIGNORED — the repo
    excludes all third-party PDFs; re-download from the lesson page).

    From the repo root (two calls, ~30s):
        .venv/bin/python academy/course-c-claude-api/exercises/34-pdf-support.py

    MEASURED 3 Sep 2026, claude-sonnet-4-5, earth.pdf (4 pages, 866KB):
        one-sentence summary: input_tokens 9625, 4.1s
            -> ~2,400 input tokens PER PAGE (text + the page rendered as
               an image). Four pages of PDF cost ~6x exercise 33's whole
               satellite photo. Pages, not kilobytes, set the bill.
        extraction: all three figures returned EXACTLY as printed,
            including Wikipedia's thin-space digit grouping —
            "6 378.137 km", "365.256 363 004 d", "70.8%". The verbatim
            spacing is the tell that it read the infobox rather than
            answering from world knowledge; a summary alone could never
            prove that.
"""

import base64
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-sonnet-4-5"
PDF = Path(__file__).parent / "earth.pdf"


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


def document_block(path):
    """The lesson's four renames from the image block, in one place."""
    with open(path, "rb") as f:
        file_bytes = base64.standard_b64encode(f.read()).decode("utf-8")
    return {
        "type": "document",                      # was "image"
        "source": {
            "type": "base64",
            "media_type": "application/pdf",     # was "image/png"
            "data": file_bytes,                  # was image_bytes
        },
    }


def ask_about_pdf(prompt):
    messages = []
    add_user_message(messages, [document_block(PDF),
                                {"type": "text", "text": prompt}])
    t0 = time.perf_counter()
    response = chat(messages)
    elapsed = time.perf_counter() - t0
    print(f"input_tokens={response.usage.input_tokens} "
          f"output_tokens={response.usage.output_tokens} elapsed={elapsed:.1f}s")
    return response


# ----------------------------- stage 1: the lesson's call, token bill seen
print("=" * 70)
print("STAGE 1 — the lesson's exact task: one-sentence summary")
print("=" * 70)
print(f"{PDF.name}: {PDF.stat().st_size // 1024}KB, 4 pages")
response = ask_about_pdf("Summarize the document in one sentence")
print(f"\n{text_from_message(response)}")

# --------------- stage 2: extraction beyond prose — a checkable data point
# "Claude can extract tables and data" is testable: ask for named figures
# from the article's infobox and check them against known values, instead
# of accepting a summary that could be written from world knowledge alone.
print()
print("=" * 70)
print("STAGE 2 — verifiable extraction: named figures from the document")
print("=" * 70)
response = ask_about_pdf(
    "From this document only, extract: (1) Earth's equatorial radius, "
    "(2) its orbital period in days, and (3) the percentage of the surface "
    "covered by water. Quote each figure exactly as printed, and say NOT "
    "STATED for anything the document does not contain."
)
print(f"\n{text_from_message(response)}")

# NOTES FROM THE COURSE
# - The four changes from image code: .pdf file, file_bytes name,
#   type "document", media_type "application/pdf". Nothing else moves.
# - Claude reads text, embedded images/charts, tables and structure — a
#   one-stop document parser, no OCR pipeline in front.
# - The lesson's demo: a Wikipedia "Earth" article PDF summarised in one
#   sentence.
#
# WORTH KNOWING (D2/D5)
# - "Summarise" is a weak parse test — the model could write it from
#   world knowledge without reading page 3. Quote-exactly-or-NOT-STATED
#   extraction is falsifiable, which is what makes stage 2 a check and
#   not a demo.
# - The per-page image rendering is why PDF input costs multiples of the
#   same text pasted raw — and why the token bill scales with pages, not
#   kilobytes.
