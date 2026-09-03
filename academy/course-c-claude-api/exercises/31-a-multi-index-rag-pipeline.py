"""
Exercise 31 — a multi-index RAG pipeline.

Course C, section: "A Multi-Index RAG pipeline" (RAG block, final section).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287766
    Code from the official 005_hybrid.ipynb; Retriever lives in
    retriever.py (course scaffolding — its header carries the score-
    direction flip and the id(doc) identity subtlety).

WHAT THIS TEACHES
    Hybrid search: one Retriever wrapping both indexes behind one
    interface, merging their rankings with Reciprocal Rank Fusion:
        RRF_score(d) = sum_i  1 / (k_rrf + rank_i(d))
    RANKS are fused, never raw scores — a cosine distance and a BM25
    score are incommensurable numbers, but first-place is first-place in
    any index. A document that places well EVERYWHERE beats a document
    that tops one list and vanishes from the other (the lesson's worked
    example: ranks 1+2 -> 0.833 beats ranks 3+1 -> 0.75 at k_rrf=1).

    The architectural point outlives RAG: because VectorIndex and
    BM25Index share the SearchIndex protocol, the Retriever composes them
    without knowing what they are — add a graph index or a domain index
    tomorrow by implementing two methods. Same move as exercise 22's
    run_tool router: uniform interface, swappable engines.

EXAM LINK
    D5 — hybrid retrieval is the production default precisely because
    real query streams mix both classes (meanings and identifiers).
    D2 — protocol-driven composition; the Retriever is to indexes what
    the router is to tools. D4 — the fused ranking is as checkable as
    either index alone: same known-question eval, run per index AND
    fused, tells you what the fusion is actually buying.

RUN
    From the repo root. Needs VOYAGE_API_KEY in the course .env.
        .venv/bin/python academy/course-c-claude-api/exercises/31-a-multi-index-rag-pipeline.py

    MEASURED 3 Sep 2026 (k=3, k_rrf=60):
        ID query:      fused 0.03279 Engineering | 0.03226 preamble
                       | 0.03150 Financial
        meaning query: fused 0.03279 Engineering | 0.03200 preamble
                       | 0.03200 Medical            <- EXACT TIE
    Engineering topped both indexes on both queries -> 1/61 + 1/61 =
    0.03279, the maximum possible fused score at k_rrf=60.
    The tie is the best RRF illustration in the run: preamble was ranked
    (2nd bm25, 3rd semantic) and Medical (3rd bm25, 2nd semantic) —
    mirrored positions, identical sum. RRF sees only rank positions, so
    mirrored disagreements cancel exactly; and at k_rrf=60 adjacent ranks
    differ by under 3% — which is why the lesson demos with k_rrf=1.

    THE RATE-LIMIT SAGA, run 1 and 2 — worth more than the fused scores:
      run 1 died on VoyageAI's keyless free tier (3 requests/min): index
      build + 2 embeds per query (the per-index display AND
      retriever.search each embedded the same question) = 4th call inside
      a minute -> RateLimitError.
      Fixes were architectural, not "retry harder": CACHE the query
      embedding (one call now serves display + fusion) and THROTTLE to
      the documented limit. Run 2 then failed IMMEDIATELY — the limit is
      enforced per ACCOUNT over a trailing minute, so run 1's calls were
      still in the window and a per-process throttle could not see them.
      Waited 70s, clean run with two visible 21s waits (D5: rate limits
      are an account property; put the limiter or cache at the shared
      boundary, not inside each script).
"""

import re
import time
from pathlib import Path

import voyageai
from dotenv import load_dotenv

from bm25_index import BM25Index
from retriever import Retriever
from vector_index import VectorIndex

load_dotenv()

client = voyageai.Client()

REPORT_PATH = Path(__file__).parent / "report.md"


def chunk_by_section(document_text):
    return re.split(r"\n## ", document_text)


# VoyageAI's keyless free tier allows 3 requests/min — the first run of
# this file hit it (RateLimitError after the 4th call in under a minute).
# Two fixes, both architectural rather than "retry harder":
#   - CACHE query embeddings: the per-index display and retriever.search
#     both embed the same question; one API call now serves both
#   - THROTTLE to the documented limit for the calls that remain
_query_cache = {}
_last_call = [0.0]


def _throttled_embed(input, model, input_type):
    wait = 21 - (time.monotonic() - _last_call[0])
    if wait > 0:
        print(f"    (rate limit: waiting {wait:.0f}s — free tier is 3 req/min)",
              flush=True)
        time.sleep(wait)
    result = client.embed(input, model=model, input_type=input_type)
    _last_call[0] = time.monotonic()
    return result


def generate_embedding(chunks, model="voyage-3-large", input_type="query"):
    is_list = isinstance(chunks, list)
    if not is_list and (chunks, input_type) in _query_cache:
        return _query_cache[(chunks, input_type)]

    input = chunks if is_list else [chunks]
    result = _throttled_embed(input, model, input_type)

    if is_list:
        return result.embeddings
    _query_cache[(chunks, input_type)] = result.embeddings[0]
    return result.embeddings[0]


# ------------------------------------------------- build the hybrid stack
chunks = chunk_by_section(REPORT_PATH.read_text())

vector_index = VectorIndex(embedding_fn=generate_embedding)
bm25_index = BM25Index()
retriever = Retriever(bm25_index, vector_index)

# ONE add_documents call: the Retriever hands the SAME dict objects to
# both indexes — which is what lets RRF recognise a document across
# result lists (identity is id(doc); see retriever.py).
retriever.add_documents([{"content": chunk} for chunk in chunks])
print(f"retriever over: {bm25_index!r}\n                {vector_index!r}")


def first_line(doc):
    return doc["content"].split("\n")[0][:44]


def hybrid_search(question, k=3):
    """Fused result plus each index's own ranking, so the fusion is
    visible instead of magical."""
    print(f"\nquery: {question!r}")
    for name, index in (("bm25    ", bm25_index), ("semantic", vector_index)):
        ranks = " > ".join(first_line(doc)[:30]
                           for doc, _ in index.search(question, k))
        print(f"  {name} ranks: {ranks}")
    results = retriever.search(question, k)
    print("  fused (RRF, higher = better):")
    for doc, score in results:
        print(f"    {score:.5f}  {first_line(doc)}")
    return results


# Both query classes from exercises 29-30, now against the fused pipeline.
hybrid_search("What happened with INC-2026-Q3-042?")
hybrid_search("How many bugs did engineers fix this year?")

# NOTES FROM THE COURSE
# - Retriever = coordinator: forward the query to every index, over-fetch
#   (k*5 each), fuse by rank with RRF, return top k.
# - RRF fuses RANK POSITIONS because raw scores from different methods
#   are not comparable. k_rrf (default 60) softens the difference between
#   adjacent ranks; the lesson uses k_rrf=1 in its worked example for
#   legibility.
# - Consistent APIs are what make the composition trivial — any new
#   search method that implements add_document(s)/search joins the fusion
#   untouched.
#
# WORTH KNOWING (Domain 5 / Domain 2)
# - Score-direction whiplash: the indexes speak lower-is-better, the
#   fusion speaks higher-is-better. Every boundary that flips a
#   convention is a latent sort(reverse=...) bug — normalise at ONE
#   layer in production code.
# - id(doc) as the fusion key works only while every index holds the
#   same object. Serialise the corpus (separate processes, a real vector
#   DB) and the fusion silently stops merging — content hashes or stable
#   doc ids are the fix.
# - This closes the RAG block's retrieval story: chunk (27) -> embed (28)
#   -> vector search (29) -> lexical search (30) -> fusion (31). Claude
#   has not appeared since exercise 26 — retrieval is model-free
#   infrastructure, testable as such.
