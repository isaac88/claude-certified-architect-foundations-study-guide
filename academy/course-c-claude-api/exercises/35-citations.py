"""
Exercise 35 — citations.

Course C, section: "Citations" (Features of Claude block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287771

WHAT THIS TEACHES
    Two fields on the document block — "title" and "citations":
    {"enabled": True} — change the RESPONSE SHAPE: the answer arrives as
    many text blocks, and blocks whose claims come from the document carry
    a .citations list. Each citation names cited_text, document_index,
    document_title, and a LOCATION whose form depends on the source type:
    - PDF source   -> page_location: start/end_page_number (1-indexed)
    - text source  -> char_location: start/end_char_index
    The answer stops being a black box: every grounded sentence points
    back into the source, and the pointer is machine-checkable.

EXAM LINK
    D5 + D2 — this is the DETERMINISTIC half of exercise 05 (D1.3)'s
    citation lesson: subagents logged sources but synthesis dropped them;
    here the API carries claim->source pairing in STRUCTURE, not prose.
    Exercise 26 got citations free with web search; this is the same
    mechanism pointed at OUR documents.

DIVERGENCES
    - None in the lesson's code. Block model claude-sonnet-4-5; chat()
      without temperature (SDK 1.2.0).
    - Current-API notes: citations are ALL-OR-NONE — with several document
      blocks, enabling citations on some but not all is a 400; and
      citations are incompatible with output_config.format (structured
      outputs) — also a 400. Choose per request: cited prose or schema.

RUN
    Needs earth.pdf next to this file (gitignored, exercise 34) and the
    RAG corpus exercises/report.md (in the repo).

    From the repo root (two calls, ~1 minute):
        .venv/bin/python academy/course-c-claude-api/exercises/35-citations.py

    MEASURED 3 Sep 2026, claude-sonnet-4-5:
        PDF stage: 3 blocks, 2 carrying citations. cited_text arrived
            with Wikipedia's own "[42]"/"[43]" reference markers embedded
            — cited_text is the RAW page text, not a cleaned quote. Both
            citations said "pages 4-5" on a FOUR-page PDF: end_page_number
            is exclusive; render page ranges accordingly or the UI names
            a page that does not exist.
        text stage: 1 citation, chars 1234-1440; slicing the source at
            those offsets reproduced cited_text EXACTLY (True) — the
            lesson's "pinpoint" claim, machine-verified.
        two free specimens:
            - The uncited block was the honest one: "the document does not
              provide information about the root cause" — grounded claims
              carry citations, the model's own reasoning does not. The
              citation/no-citation split labels which is which.
            - The cited claim says the outage "occurred during the
              cutover"; the quote only says the migration completed and
              one outage was closed in four hours. The inference LEAKED
              past the evidence — and the citation is what makes the
              overreach visible and checkable. That is the feature.
"""

import base64
import time
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic()

MODEL = "claude-sonnet-4-5"
HERE = Path(__file__).parent


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


def pdf_document_block(path, title):
    with open(path, "rb") as f:
        file_bytes = base64.standard_b64encode(f.read()).decode("utf-8")
    return {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": file_bytes,
        },
        "title": title,                      # new
        "citations": {"enabled": True},      # new
    }


def text_document_block(text, title):
    return {
        "type": "document",
        "source": {
            "type": "text",
            "media_type": "text/plain",
            "data": text,
        },
        "title": title,
        "citations": {"enabled": True},
    }


def show_cited_response(response, elapsed):
    """Render the multi-block answer as footnoted text + a sources list —
    the terminal version of the lesson's hover UI."""
    footnotes = []
    answer = ""
    for block in response.content:
        if block.type != "text":
            continue
        answer += block.text
        for c in (block.citations or []):
            footnotes.append(c)
            answer += f"[{len(footnotes)}]"

    print(f"blocks: {len(response.content)}  "
          f"cited blocks: {sum(1 for b in response.content if b.type == 'text' and b.citations)}  "
          f"citations: {len(footnotes)}  elapsed={elapsed:.1f}s")
    print(f"\n{answer.strip()}\n")
    for i, c in enumerate(footnotes, 1):
        if c.type == "page_location":
            where = f"pages {c.start_page_number}-{c.end_page_number}"
        elif c.type == "char_location":
            where = f"chars {c.start_char_index}-{c.end_char_index}"
        else:
            where = c.type
        quote = " ".join(c.cited_text.split())[:110]
        print(f'  [{i}] {c.document_title}, {where}: "{quote}..."')
    return footnotes


# --------------------------- stage 1: PDF citations come as page locations
print("=" * 70)
print("STAGE 1 — earth.pdf, the lesson's question; citations by PAGE")
print("=" * 70)
messages = []
add_user_message(messages, [
    pdf_document_block(HERE / "earth.pdf", "earth.pdf"),
    {"type": "text", "text": "How did Earth's atmosphere form?"},
])
t0 = time.perf_counter()
response = chat(messages)
show_cited_response(response, time.perf_counter() - t0)

# --------------- stage 2: text citations come as char offsets — CHECK them
# Plain-text source: our own RAG corpus. The lesson says char positions
# "pinpoint exactly" where each fact lives — with a text source that claim
# is machine-checkable: slice the source at the returned indices and
# compare with cited_text. Verification, not trust.
print()
print("=" * 70)
print("STAGE 2 — plain-text source (report.md); citations by CHAR OFFSET")
print("=" * 70)
article_text = (HERE / "report.md").read_text()

messages = []
add_user_message(messages, [
    text_document_block(article_text, "quarterly_report"),
    {"type": "text", "text": "What happened in incident INC-2026-Q3-042, "
                             "and what was the root cause?"},
])
t0 = time.perf_counter()
response = chat(messages)
footnotes = show_cited_response(response, time.perf_counter() - t0)

print("\nSlicing the source at each citation's char range:")
mismatches = 0
for i, c in enumerate(footnotes, 1):
    if c.type != "char_location":
        continue
    sliced = article_text[c.start_char_index:c.end_char_index]
    ok = sliced == c.cited_text
    mismatches += (not ok)
    print(f"  [{i}] source[{c.start_char_index}:{c.end_char_index}] "
          f"== cited_text: {ok}")
print("-> every offset resolves to its exact quote" if not mismatches
      else f"-> {mismatches} MISMATCH(ES) — offsets cannot be trusted blind")

# NOTES FROM THE COURSE
# - Enabling: "title" + "citations": {"enabled": True} on the document
#   block. PDF sources cite by page; text sources by char position.
# - Citation fields: cited_text, document_index, document_title, and
#   start/end page numbers (PDF) or char indices (text).
# - The value is the UI it enables: hover a claim, see the exact passage —
#   Claude as a research assistant that shows its work, not a black box.
# - Use when users must verify, sources are authoritative, transparency
#   is required, or readers will want the surrounding context.
#
# WORTH KNOWING (D2/D5)
# - cited_text is EVIDENCE, not decoration: stage 2 verifies each char
#   range against the source. A pipeline can reject any answer whose
#   citations fail this check — a deterministic gate on grounding.
# - The multi-block response is the third response-shape change of this
#   course (tool_use blocks, thinking blocks, now citation-bearing text
#   splits). Code that assumes one text block keeps being wrong.
