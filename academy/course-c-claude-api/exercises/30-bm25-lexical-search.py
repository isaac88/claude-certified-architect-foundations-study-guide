"""
Exercise 30 — BM25 lexical search.

Course C, section: "BM25 lexical search" (RAG block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287767
    Code from the official 005_hybrid.ipynb; BM25Index lives in
    bm25_index.py (course scaffolding — its header lists three sharp
    edges: piecewise tokenisation of IDs, no stemming, lower-is-better
    normalised scores).

WHAT THIS TEACHES
    Semantic search misses what it cannot MEAN: an incident ID like
    INC-2026-Q3-042 has no meaning, only identity, and an embedding can
    only place it "somewhere technical". Lexical search inverts the trade:
    BM25 scores documents by weighted exact-token overlap —
        tokenize -> weight rare terms high (IDF) -> reward term frequency
        with diminishing returns (k1) -> damp long documents (b)
    — so a rare token like an incident ID dominates its query.

    The two searches fail on each other's strengths, which is the whole
    argument for running BOTH (the Retriever, next section):
        semantic wins   "how many bugs did engineers fix" — meaning
                        disambiguates bug-the-defect from bug-the-insect
        lexical wins    "what happened with INC-2026-Q3-042" — identity
                        has no meaning to embed
    This exercise measures both queries against both indexes on the same
    five chunks, so the complementarity is a table, not a slogan.

DATA NOTE
    report.md gained one sentence for this lesson (the incident ID in the
    engineering section). Exercise 29's recorded distances predate that
    edit; re-runs will shift a little.

EXAM LINK
    D5 — retrieval architecture: neither index is "better"; they cover
    different query classes, and real corpora receive both classes. D1
    echo — this is dynamic-vs-deterministic again: embeddings judge by
    meaning (fuzzy, generalises), BM25 by literal tokens (exact,
    brittle-but-precise). Hybrid = use each where its guarantees hold.

RUN
    From the repo root. Needs VOYAGE_API_KEY in the course .env.
        .venv/bin/python academy/course-c-claude-api/exercises/30-bm25-lexical-search.py

    MEASURED 3 Sep 2026, 5 chunks, lower = better on both indexes:
        ID query ("What happened with INC-2026-Q3-042?"):
            semantic  0.5753 Engineering   0.6680 (preamble)
            bm25      0.6157 Engineering   0.8611 (preamble)
        meaning query ("How many bugs did engineers fix this year?"):
            semantic  0.3584 Engineering   0.5081 Medical
            bm25      0.7143 Engineering   0.9220 (preamble)

    BOTH indexes answered BOTH queries correctly — five chunks is too
    small a corpus to make either fail, and saying so beats faking a
    failure. The lesson's argument lives in the MARGINS:
      - semantic's ID match was its weakest-confidence result of the day
        (0.575 vs 0.358): it matched the CONTEXT around the ID ("outage",
        "incident"), not the identifier. Scale the corpus and that margin
        is how the wrong incident gets retrieved.
      - bm25 dodged the bug-bites trap BY ACCIDENT of morphology: query
        "bugs" matched engineering's "bugs" and simply failed to match
        medical's singular "bug" — no stemming cut in our favour. Stem
        the tokens (as real deployments do) or ask with the singular and
        the lexical trap fires exactly as designed.
    Complementarity is real, but it shows at scale and in margins — a
    toy corpus demonstrates the mechanics, not the failure rates (D4:
    that is what a retrieval eval on real data is for).
"""

import re
from pathlib import Path

import voyageai
from dotenv import load_dotenv

from bm25_index import BM25Index
from vector_index import VectorIndex

load_dotenv()

client = voyageai.Client()

REPORT_PATH = Path(__file__).parent / "report.md"


def chunk_by_section(document_text):
    return re.split(r"\n## ", document_text)


def generate_embedding(chunks, model="voyage-3-large", input_type="query"):
    is_list = isinstance(chunks, list)
    input = chunks if is_list else [chunks]
    result = client.embed(input, model=model, input_type=input_type)
    return result.embeddings if is_list else result.embeddings[0]


# ---------------------------------------------------- build BOTH indexes
chunks = chunk_by_section(REPORT_PATH.read_text())
documents = [{"content": chunk} for chunk in chunks]

# Semantic index: embedding_fn wired in, so add_documents batch-embeds
# and search() accepts a plain string (it embeds the query itself).
vector_index = VectorIndex(embedding_fn=generate_embedding)
vector_index.add_documents(documents)

# Lexical index: pure local computation — no API, no key, no cost.
bm25_index = BM25Index()
bm25_index.add_documents(documents)

print(f"indexes: {vector_index!r}")
print(f"         {bm25_index!r}")


def compare(question, k=2):
    """Same question, both indexes. Both report lower-is-better scores."""
    print(f"\nquery: {question!r}")
    for name, index in (("semantic", vector_index), ("bm25    ", bm25_index)):
        results = index.search(question, k)
        summary = "  |  ".join(
            f"{score:.4f} {doc['content'].split(chr(10))[0][:34]}"
            for doc, score in results
        )
        print(f"  {name}  {summary if summary else '(no match at all)'}")


# The lesson's case: an identifier — identity, not meaning.
compare("What happened with INC-2026-Q3-042?")

# Exercise 29's case: meaning, not identity.
compare("How many bugs did engineers fix this year?")

# NOTES FROM THE COURSE
# - BM25 steps: tokenize -> corpus term frequencies -> IDF-weight (rare =
#   important, "a" = noise) -> best-matching documents win.
# - Run semantic and lexical IN PARALLEL and merge — hybrid search. The
#   merging (Reciprocal Rank Fusion) is the next section.
# - BM25 shines on technical terms, IDs, exact phrases — the queries
#   embeddings blur.
#
# WORTH KNOWING (Domain 5)
# - BM25 is LOCAL and free: no API call, no key, no per-query cost, no
#   latency. The semantic side bills and waits per query. In a hybrid,
#   the expensive index should earn its place on the query classes BM25
#   cannot serve.
# - No stemming means "fix" never matches "fixed". Real deployments add
#   stemming/analysis at the tokenizer — which is why BM25Index accepts a
#   custom tokenizer argument.
# - The exp(-0.1*raw) normalisation exists purely so both indexes speak
#   lower-is-better — interface unification for the Retriever, not
#   statistics.
