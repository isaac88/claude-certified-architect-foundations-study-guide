"""
Exercise 27 — text chunking strategies.

Course C, section: "Text chunking strategies" (RAG block; the intro
section "Introducing Retrieval Augmented Generation" has no code).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287776
    Code from the official 001_chunking.ipynb.

WHAT THIS TEACHES
    RAG step zero: how a document is cut decides what retrieval can ever
    find. A bad cut puts the medical section's "bug bites" into the chunk
    that answers "how many bugs did engineers fix?" — the wrong context
    goes into the prompt, and the model answers confidently from it.

    Four strategies, one trade-off axis (chunk quality vs guarantees you
    need about the input):
      size-based       equal character slices (+ overlap). Works on ANY
                       input, including code; cuts words mid-stream.
                       Production's default fallback.
      sentence-based   split on sentence enders, group N per chunk with
                       overlap. Middle ground for prose.
      structure-based  split on document structure (\\n## for Markdown).
                       Cleanest chunks — but only when the format is
                       GUARANTEED. A PDF with no headers gets one chunk.
      semantic-based   group sentences by meaning-similarity. Best chunks,
                       highest cost; described in the lesson, implemented
                       by nobody here (needs embeddings — next section).

    The decision is 1.1's rule wearing RAG clothes: the strategy's
    assumptions must match the input's guarantees. Structure-based on
    uncontrolled input is the hardcoded pipeline on variable input.

NOTE ON THE DATA
    The course's report.md was not in ~/Downloads, so exercises/report.md
    here is a stand-in written to the lesson's description: mixed
    medical / engineering / finance sections, with the "bug" ambiguity
    planted (medical "bug bites" vs engineering "fixed 128 bugs") for the
    later retrieval lessons to trip over. Swap in the course's file and
    re-run if you download it.

TWO LATENT BUGS IN THE COURSE'S CHUNKERS — noted, not triggered
    - chunk_by_char: if chunk_overlap >= chunk_size, start_idx never
      advances -> infinite loop.
    - chunk_by_sentence: if overlap_sentences >= max_sentences_per_chunk,
      the step is 0 or negative -> infinite loop. Its `if start_idx < 0`
      guard resets to 0, which makes the loop TIGHTER, not safer.
    Both are the same defect: a loop whose step is caller-controlled with
    no validation. Fine in a lesson; in production, validate parameters
    at the top or the pipeline hangs on someone's config edit.

EXAM LINK
    D5 (context quality) — the chunker decides what CAN be retrieved;
    every downstream answer inherits its cuts. D1-adjacent — choose the
    deterministic strategy by the input's variability, per document type,
    not one-size-for-all.

RUN
    From the repo root (no API calls — pure Python):
        .venv/bin/python academy/course-c-claude-api/exercises/27-text-chunking-strategies.py

    MEASURED 3 Sep 2026, on the 2,351-char stand-in report.md:
        chunk_by_char(150, 20):   18 chunks — cut landed mid-clause
                                  ("...software\\nengineering, and" echoed
                                  at chunk 1's start by the overlap)
        chunk_by_sentence(5, 1):   7 chunks — every boundary a sentence
        chunk_by_section:          5 chunks — one per section, PLUS chunk 0
                                  holding the pre-header title/preamble,
                                  and '## ' stripped from every other
                                  chunk (re.split consumed the delimiter)
"""

import re
from pathlib import Path

REPORT_PATH = Path(__file__).parent / "report.md"


# ------------------------------------------------- size-based (characters)
def chunk_by_char(text, chunk_size=150, chunk_overlap=20):
    chunks = []
    start_idx = 0

    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))
        chunks.append(text[start_idx:end_idx])

        # Step back by the overlap so each chunk re-carries the tail of
        # the previous one — context glue across the cut.
        start_idx = (
            end_idx - chunk_overlap if end_idx < len(text) else len(text)
        )

    return chunks


# --------------------------------------------------------- sentence-based
def chunk_by_sentence(text, max_sentences_per_chunk=5, overlap_sentences=1):
    # Split AFTER . ! ? followed by whitespace — lookbehind keeps the
    # punctuation attached to its sentence.
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    start_idx = 0

    while start_idx < len(sentences):
        end_idx = min(start_idx + max_sentences_per_chunk, len(sentences))
        chunks.append(" ".join(sentences[start_idx:end_idx]))

        start_idx += max_sentences_per_chunk - overlap_sentences

        if start_idx < 0:      # the notebook's guard — see the header note
            start_idx = 0

    return chunks


# -------------------------------------------------------- structure-based
def chunk_by_section(document_text):
    pattern = r"\n## "
    return re.split(pattern, document_text)


# ------------------------------------------------------------------ run
text = REPORT_PATH.read_text()
print(f"document: {REPORT_PATH.name}, {len(text)} chars\n")

# --- size-based: reliable, and visibly crude at the boundaries
char_chunks = chunk_by_char(text)
print(f"chunk_by_char(150, overlap=20): {len(char_chunks)} chunks")
print(f"  chunk 0 ends:   ...{char_chunks[0][-40:]!r}")
print(f"  chunk 1 starts: {char_chunks[1][:40]!r}")
print("  ^ the 20-char overlap repeats the tail; the cut lands mid-word\n")

# --- sentence-based: boundaries are always sentence boundaries
sentence_chunks = chunk_by_sentence(text)
print(f"chunk_by_sentence(5, overlap=1): {len(sentence_chunks)} chunks")
print(f"  chunk 1: {sentence_chunks[1][:100]!r}...")
print("  ^ starts at a sentence start, ends at a sentence end\n")

# --- structure-based: one chunk per section, headers intact-ish
section_chunks = chunk_by_section(text)
print(f"chunk_by_section: {len(section_chunks)} chunks")
for i, chunk in enumerate(section_chunks):
    first_line = chunk.split("\n")[0][:60]
    print(f"  [{i}] {len(chunk):4d} chars | {first_line}")
print("  ^ note: re.split CONSUMES the '\\n## ' delimiter — every chunk"
      "\n    after the first has lost its '## ' marker, and chunk 0 is"
      "\n    everything before the first header (title + preamble).")

# NOTES FROM THE COURSE
# - No universally best strategy: match the chunker to the guarantees you
#   hold about the documents.
# - Structure-based when you CONTROL the format (internal reports);
#   sentence-based as prose middle ground; size-based + overlap as the
#   production fallback that never breaks, even on code.
# - Overlap exists to stop boundary losses: whole words/sentences and the
#   header-content connection.
# - Semantic chunking: group sentences by relatedness. Best quality,
#   highest compute, needs sentence meaning — foreshadows embeddings.
#
# WORTH KNOWING (Domain 5)
# - The chunker is a DETERMINISTIC preprocessing stage — get it wrong and
#   no amount of model quality downstream recovers the lost context. Trace
#   a bad RAG answer to origin and the origin is often here.
# - chunk_by_section keeping the pre-header preamble as chunk 0 and
#   stripping '## ' markers are exactly the boundary details a retrieval
#   debug session ends up staring at. Know what your splitter throws away.
# - The overlap parameters are a context-budget dial: more overlap = fewer
#   boundary losses but more duplicated tokens per retrieved chunk (D5
#   pays that bill on every prompt).
