"""
Exercise 28 — text embeddings.

Course C, section: "Text embeddings" (RAG block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287759

WHAT THIS TEACHES
    Retrieval is a search problem: which chunks relate to the question?
    Semantic search answers it with EMBEDDINGS — a numerical fingerprint
    of a text's MEANING:
        text -> embedding model -> a long vector of floats in [-1, +1]
    Each number scores some learned quality of the text. Which quality,
    nobody knows — "dimension 412 = talks about oceans" is a helpful
    fiction. The dimensions are learned, not labelled; the vector is only
    useful COMPARED to other vectors (next section's material).

    Anthropic does not sell embeddings; the course (and Anthropic's docs)
    point to VoyageAI. Separate account, separate key:
        VOYAGE_API_KEY=... in this folder's .env
    (free tier is fine for the course).

    One parameter the lesson shows but does not dwell on — input_type:
        "document"  for the chunks you index
        "query"     for the question you search with
    Voyage embeds the two ASYMMETRICALLY, tuning each side of the search
    for its role. Embedding everything as "query" (the lesson function's
    default) works, but the pairing is the intended use and measurably
    better at retrieval. Sort your texts into their roles.

EXAM LINK
    D5 — RAG's second stage: the chunker (ex. 27) decides what CAN be
    found; the embedding decides what LOOKS similar. Both are upstream of
    the model, and both are where bad answers are born.
    D2-adjacent — a second external service in the pipeline: its own key,
    its own rate limits, its own failure modes to propagate honestly.

RUN
    From the repo root. Needs VOYAGE_API_KEY in
    academy/course-c-claude-api/.env (sign up at voyageai.com).
        .venv/bin/python academy/course-c-claude-api/exercises/28-text-embeddings.py

    MEASURED 3 Sep 2026, voyage-3-large:
        chunk  (input_type="document"): 1024 dims, values -0.1097..+0.1040
        query  (input_type="query"):    1024 dims
    Two observations:
      - a 557-char report section and a 9-word question map to vectors of
        the SAME length — the shared space is the whole mechanism
      - the values live in ±0.11, nowhere near the stated ±1 bounds. The
        lesson's "each number ranges from -1 to +1" is the RANGE of the
        format, not the typical magnitude: unit-normalised vectors spread
        small values across 1024 dimensions. Expect hundredths, not ones.
"""

import os
import re
import sys
from pathlib import Path

import voyageai
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("VOYAGE_API_KEY"):
    sys.exit(
        "VOYAGE_API_KEY is not set. Sign up at https://www.voyageai.com, "
        "create a key, and add VOYAGE_API_KEY=... to "
        "academy/course-c-claude-api/.env (free tier is fine)."
    )

client = voyageai.Client()          # reads VOYAGE_API_KEY from the env

REPORT_PATH = Path(__file__).parent / "report.md"


def generate_embedding(text, model="voyage-3-large", input_type="query"):
    """The lesson's function: one text in, one vector out. client.embed
    takes a LIST of texts (batching is the normal case); we send one and
    take the first result."""
    result = client.embed([text], model=model, input_type=input_type)
    return result.embeddings[0]


def chunk_by_section(document_text):
    return re.split(r"\n## ", document_text)


# ------------------------------------------------------------------ run
chunks = chunk_by_section(REPORT_PATH.read_text())
engineering_chunk = next(c for c in chunks if c.startswith("Software Engineering"))

# The corpus side: a chunk, embedded as a document.
chunk_embedding = generate_embedding(engineering_chunk, input_type="document")

print(f"chunk: {engineering_chunk[:60]!r}...")
print(f"embedding length: {len(chunk_embedding)}")
print(f"value range:      {min(chunk_embedding):+.4f} .. {max(chunk_embedding):+.4f}")
print(f"first 5 values:   {[round(v, 4) for v in chunk_embedding[:5]]}")

# The search side: a question, embedded as a query.
question = "How many bugs did engineers fix this year?"
query_embedding = generate_embedding(question, input_type="query")

print(f"\nquery: {question!r}")
print(f"embedding length: {len(query_embedding)}")
print(f"first 5 values:   {[round(v, 4) for v in query_embedding[:5]]}")

print("\nSame length, wildly different texts — every text maps into the SAME")
print("vector space. That is the whole trick: once question and chunks live")
print("in one space, 'relevant' becomes 'nearby', and comparing vectors is")
print("the next section.")

# NOTES FROM THE COURSE
# - Embedding = numerical representation of meaning; floats in [-1, +1];
#   each dimension scores some learned, unlabelled quality.
# - Do not over-interpret single dimensions — the "happiness score"
#   framing is a teaching fiction.
# - VoyageAI because Anthropic has no embeddings API. Separate key, in
#   .env, never in code (same rule as ANTHROPIC_API_KEY).
# - generate_embedding wraps client.embed([text], model, input_type).
#
# WORTH KNOWING (Domain 5)
# - The embedding VECTOR is useless alone; retrieval quality lives in the
#   GEOMETRY — which texts end up near which. Model choice and input_type
#   both move that geometry, so changing embedding model silently
#   re-ranks your entire corpus: re-run the retrieval eval after (D4).
# - Embed once, store, reuse: chunks are embedded at INDEX time, queries
#   at SEARCH time. Only the query costs money per user request.
# - pip install voyageai pulled ~35 packages including numpy and
#   langchain-core — supply-chain weight worth knowing about before it
#   lands in a production image.
