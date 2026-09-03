"""
Exercise 29 — implementing the RAG flow.

Course C, sections: "The full RAG flow" (concept, no code) +
"Implementing the RAG flow" (RAG block).
SOURCE
    https://anthropic.skilljar.com/claude-with-the-anthropic-api
    https://anthropic.skilljar.com/claude-with-the-anthropic-api/287761
    Code from the official 003_vectordb.ipynb; VectorIndex lives in
    vector_index.py (course scaffolding module — see its header, including
    the notebook's add_documents bug).

WHAT THIS TEACHES
    The five retrieval steps, end to end and by hand:
      1. chunk the text by section
      2. embed every chunk           (ONE batched API call)
      3. store vector+text pairs in a VectorIndex
      4. embed the user's question
      5. search: distance to every stored vector, smallest k win
    Steps 1-3 happen at INDEX time, once per document. Steps 4-5 happen
    per question. The only model in sight is the embedding model — no
    Claude call yet; generation joins the pipeline later.

    Why store the original text next to each vector: a search that
    returns numbers is useless — the text is what goes into the prompt.
    The vector is the index key; the chunk is the payload.

DIVERGENCES / DECISIONS
    - The notebook's own demo cell calls store.add_documents (plural) —
      a method VectorIndex does not have. We follow the lesson text:
      batch-embed, then add_vector per (embedding, chunk) pair.
    - input_type: chunks are embedded as "document", the question as
      "query" — the role pairing recorded in exercise 28. The lesson
      leaves everything on the default "query"; this is a deliberate,
      noted improvement, not drift.
    - The course's report.md has different sections (theirs shows a
      "Methodology" chunk at distance 0.72); ours is the stand-in from
      exercise 27, so distances differ. The SHAPE of the result is what
      matters: right section first, meaningful gap to second.

EXAM LINK
    D5 — the full retrieval half of RAG, with its cost profile: indexing
    is one-off, per-question cost is one query embedding + a brute-force
    scan (fine at 5 chunks; a real corpus swaps VectorIndex for ANN — same
    interface, different engine). D4 — "did retrieval get the RIGHT chunk"
    is checkable per query: it is an eval waiting to be written.

RUN
    From the repo root. Needs VOYAGE_API_KEY in the course .env.
        .venv/bin/python academy/course-c-claude-api/exercises/29-implementing-the-rag-flow.py

    MEASURED 3 Sep 2026, voyage-3-large, 5 chunks of the stand-in report:
        lesson query ("What did the software engineering dept do..."):
            0.4131  Software Engineering Updates      <- right, first
            0.4933  (title/preamble chunk)
        trap query ("How many bugs did engineers fix this year?"):
            0.3855  Software Engineering Updates      <- right, first
            0.5474  Medical Research Findings ("bug bites")

    THE TRAP FROM EXERCISE 27 SPRANG CORRECTLY: "bug" lives in both
    sections, and semantic search put defect-fixing meaning over insect
    string-matching — with a WIDE gap (0.39 vs 0.55). Medical still came
    second, which is the lexical pull showing through. Keep this run in
    mind for the BM25 section: pure keyword search faces the same trap
    with no meaning to lean on.
"""

import re
from pathlib import Path

import voyageai
from dotenv import load_dotenv

from vector_index import VectorIndex

load_dotenv()

client = voyageai.Client()

REPORT_PATH = Path(__file__).parent / "report.md"


def chunk_by_section(document_text):
    return re.split(r"\n## ", document_text)


def generate_embedding(chunks, model="voyage-3-large", input_type="query"):
    """The lesson's upgraded function: accepts one string OR a list, and
    returns the matching shape. Batching matters twice — one HTTP call
    instead of N, and it dodges VoyageAI's rate limit on the free tier."""
    is_list = isinstance(chunks, list)
    input = chunks if is_list else [chunks]
    result = client.embed(input, model=model, input_type=input_type)
    return result.embeddings if is_list else result.embeddings[0]


# ------------------------------------------------- index time (runs once)
# 1. chunk
text = REPORT_PATH.read_text()
chunks = chunk_by_section(text)
print(f"1. chunked: {len(chunks)} sections")

# 2. embed all chunks in one batched call, as documents
embeddings = generate_embedding(chunks, input_type="document")
print(f"2. embedded: {len(embeddings)} vectors of {len(embeddings[0])} dims")

# 3. store vector + original text together
store = VectorIndex()
for embedding, chunk in zip(embeddings, chunks):
    store.add_vector(embedding, {"content": chunk})
print(f"3. stored:   {store!r}")

# ---------------------------------------------- query time (per question)
def ask(question, k=2):
    print(f"\nquery: {question!r}")
    # 4. embed the question, as a query
    user_embedding = generate_embedding(question, input_type="query")
    # 5. brute-force search, smallest cosine distance wins
    results = store.search(user_embedding, k)
    for doc, distance in results:
        first_line = doc["content"].split("\n")[0][:50]
        print(f"  {distance:.4f}  {first_line}")
    return results


# The lesson's query...
ask("What did the software engineering dept do last year?")

# ...and the trap planted in report.md back in exercise 27: "bug" appears
# in BOTH the medical section (bug bites) and the engineering section
# (fixed 128 bugs). Semantic search should rank engineering first because
# the QUESTION's meaning is about defect-fixing, not insects.
ask("How many bugs did engineers fix this year?")

# NOTES FROM THE COURSE
# - Five steps: chunk -> embed chunks -> store -> embed question ->
#   search. Store the text WITH the vector or search returns nothing
#   usable.
# - Lower cosine distance = more similar (it is 1 - cosine similarity).
# - The course's run: "Software Engineering" at 0.71, "Methodology" at
#   0.72 — note how close those are; ranking, not magnitude, does the
#   work.
# - "There are scenarios where this doesn't perform as expected" — the
#   lesson's own cliffhanger; BM25 and multi-index are the responses.
#
# WORTH KNOWING (Domain 5 / Domain 4)
# - Retrieval is a per-query, checkable stage: for a known question you
#   know which chunk SHOULD come back, so retrieval accuracy is an eval
#   you can run without Claude in the loop at all. When a RAG answer is
#   wrong, test THIS stage first — it is cheaper than judging prose.
# - Distances cluster tightly (course's 0.71 vs 0.72). Never threshold on
#   absolute distance without measuring your own corpus's distribution;
#   rank is robust, magnitude is not.
