"""
Retriever — course scaffolding for the RAG block (005_hybrid.ipynb).

NOT a numbered exercise. Wraps any number of indexes that speak the
SearchIndex protocol (add_document / add_documents / search) and merges
their rankings with Reciprocal Rank Fusion:

    RRF_score(d) = sum over indexes of  1 / (k_rrf + rank_i(d))

Rank positions, not raw scores, are fused — which is the whole point:
cosine distances and BM25 scores are incommensurable numbers, but "what
came first" is comparable across any pair of indexes.

THREE THINGS TO KNOW BEFORE TRUSTING IT
    - SCORE DIRECTION FLIPS: both wrapped indexes return lower-is-better;
      RRF returns HIGHER-is-better (sorted descending). Mixed conventions
      in one file is exactly where a sort(reverse=?) bug is born.
    - DOCUMENT IDENTITY IS id(doc): fusion merges results only because
      retriever.add_document(s) hands the SAME dict object to every
      index. Add copies per index and nothing ever merges — every doc
      appears once per index, unfused. Content-based keys would be the
      robust fix.
    - It over-fetches k*5 from every index before fusing, so a document
      ranked deep in one index can still contribute to the fusion.
"""

from typing import Any, Dict, List, Protocol, Tuple


class SearchIndex(Protocol):
    def add_document(self, document: Dict[str, Any]) -> None: ...

    def add_documents(self, documents: List[Dict[str, Any]]) -> None: ...

    def search(self, query: Any, k: int = 1) -> List[Tuple[Dict[str, Any], float]]: ...


class Retriever:
    def __init__(self, *indexes: SearchIndex):
        if len(indexes) == 0:
            raise ValueError("At least one index must be provided")
        self._indexes = list(indexes)

    def add_document(self, document: Dict[str, Any]):
        for index in self._indexes:
            index.add_document(document)

    def add_documents(self, documents: List[Dict[str, Any]]):
        for index in self._indexes:
            index.add_documents(documents)

    def search(
        self, query_text: str, k: int = 1, k_rrf: int = 60
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not isinstance(query_text, str):
            raise TypeError("Query text must be a string.")
        if k <= 0:
            raise ValueError("k must be a positive integer.")
        if k_rrf < 0:
            raise ValueError("k_rrf must be non-negative.")

        all_results = [index.search(query_text, k=k * 5) for index in self._indexes]

        doc_ranks: Dict[int, Dict[str, Any]] = {}
        for idx, results in enumerate(all_results):
            for rank, (doc, _) in enumerate(results):
                doc_id = id(doc)
                if doc_id not in doc_ranks:
                    doc_ranks[doc_id] = {
                        "doc_obj": doc,
                        "ranks": [float("inf")] * len(self._indexes),
                    }
                doc_ranks[doc_id]["ranks"][idx] = rank + 1

        def calc_rrf_score(ranks: List[float]) -> float:
            return sum(1.0 / (k_rrf + r) for r in ranks if r != float("inf"))

        scored_docs: List[Tuple[Dict[str, Any], float]] = [
            (ranks["doc_obj"], calc_rrf_score(ranks["ranks"]))
            for ranks in doc_ranks.values()
        ]

        filtered_docs = [(doc, score) for doc, score in scored_docs if score > 0]
        filtered_docs.sort(key=lambda x: x[1], reverse=True)

        return filtered_docs[:k]
