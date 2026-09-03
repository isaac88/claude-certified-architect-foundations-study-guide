"""
BM25Index — course scaffolding for the RAG block (005_hybrid.ipynb).

NOT a numbered exercise. Lexical (keyword) search over the same
document-dict shape VectorIndex uses, so the two are interchangeable
behind one interface — which is what the multi-index Retriever exploits
in the next section.

HOW BM25 SCORES A DOCUMENT (per query token):
    idf         rare-in-corpus terms weigh more ("inc" beats "the")
    term_freq   more occurrences in THIS doc raise the score, with
                diminishing returns controlled by k1
    length norm long documents are damped (b) so they cannot win by
                merely containing everything

THREE SHARP EDGES worth knowing before trusting results:
    - The default tokenizer lowercases and splits on \\W+ — so the ID
      "INC-2026-Q3-042" becomes FOUR tokens: inc / 2026 / q3 / 042. It
      still wins searches because each piece is rare, but the match is
      per-piece, not exact-string.
    - NO STEMMING: "bug" and "bugs", "fix" and "fixed" are different
      tokens that never match each other. Lexical means literal.
    - search() returns exp(-0.1 * raw_score) sorted ASCENDING — LOWER is
      better, deliberately matching VectorIndex's distance convention so
      callers can treat both indexes alike.
"""

import math
import re
from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Tuple


class BM25Index:
    def __init__(
        self,
        k1: float = 1.5,
        b: float = 0.75,
        tokenizer: Optional[Callable[[str], List[str]]] = None,
    ):
        self.documents: List[Dict[str, Any]] = []
        self._corpus_tokens: List[List[str]] = []
        self._doc_len: List[int] = []
        self._doc_freqs: Dict[str, int] = {}
        self._avg_doc_len: float = 0.0
        self._idf: Dict[str, float] = {}
        self._index_built: bool = False

        self.k1 = k1
        self.b = b
        self._tokenizer = tokenizer if tokenizer else self._default_tokenizer

    def _default_tokenizer(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.split(r"\W+", text)
        return [token for token in tokens if token]

    def _update_stats_add(self, doc_tokens: List[str]):
        self._doc_len.append(len(doc_tokens))

        seen_in_doc = set()
        for token in doc_tokens:
            if token not in seen_in_doc:
                self._doc_freqs[token] = self._doc_freqs.get(token, 0) + 1
                seen_in_doc.add(token)

        self._index_built = False

    def _calculate_idf(self):
        N = len(self.documents)
        self._idf = {}
        for term, freq in self._doc_freqs.items():
            self._idf[term] = math.log(((N - freq + 0.5) / (freq + 0.5)) + 1)

    def _build_index(self):
        if not self.documents:
            self._avg_doc_len = 0.0
            self._idf = {}
            self._index_built = True
            return

        self._avg_doc_len = sum(self._doc_len) / len(self.documents)
        self._calculate_idf()
        self._index_built = True

    def add_document(self, document: Dict[str, Any]):
        if not isinstance(document, dict):
            raise TypeError("Document must be a dictionary.")
        if "content" not in document:
            raise ValueError("Document dictionary must contain a 'content' key.")

        content = document.get("content", "")
        if not isinstance(content, str):
            raise TypeError("Document 'content' must be a string.")

        doc_tokens = self._tokenizer(content)

        self.documents.append(document)
        self._corpus_tokens.append(doc_tokens)
        self._update_stats_add(doc_tokens)

    def add_documents(self, documents: List[Dict[str, Any]]):
        if not isinstance(documents, list):
            raise TypeError("Documents must be a list of dictionaries.")
        if not documents:
            return

        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                raise TypeError(f"Document at index {i} must be a dictionary.")
            if "content" not in doc:
                raise ValueError(f"Document at index {i} must contain a 'content' key.")
            if not isinstance(doc["content"], str):
                raise TypeError(f"Document 'content' at index {i} must be a string.")

            doc_tokens = self._tokenizer(doc["content"])
            self.documents.append(doc)
            self._corpus_tokens.append(doc_tokens)
            self._update_stats_add(doc_tokens)

        self._index_built = False

    def _compute_bm25_score(self, query_tokens: List[str], doc_index: int) -> float:
        score = 0.0
        doc_term_counts = Counter(self._corpus_tokens[doc_index])
        doc_length = self._doc_len[doc_index]

        for token in query_tokens:
            if token not in self._idf:
                continue

            idf = self._idf[token]
            term_freq = doc_term_counts.get(token, 0)

            numerator = idf * term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (
                1 - self.b + self.b * (doc_length / self._avg_doc_len)
            )
            score += numerator / (denominator + 1e-9)

        return score

    def search(
        self,
        query: Any,
        k: int = 1,
        score_normalization_factor: float = 0.1,
    ) -> List[Tuple[Dict[str, Any], float]]:
        if not self.documents:
            return []

        if isinstance(query, str):
            query_text = query
        else:
            raise TypeError("Query must be a string for BM25Index.")

        if k <= 0:
            raise ValueError("k must be a positive integer.")

        if not self._index_built:
            self._build_index()

        if self._avg_doc_len == 0:
            return []

        query_tokens = self._tokenizer(query_text)
        if not query_tokens:
            return []

        raw_scores = []
        for i in range(len(self.documents)):
            raw_score = self._compute_bm25_score(query_tokens, i)
            if raw_score > 1e-9:
                raw_scores.append((raw_score, self.documents[i]))

        raw_scores.sort(key=lambda item: item[0], reverse=True)

        normalized_results = []
        for raw_score, doc in raw_scores[:k]:
            normalized_score = math.exp(-score_normalization_factor * raw_score)
            normalized_results.append((doc, normalized_score))

        normalized_results.sort(key=lambda item: item[1])

        return normalized_results

    def __len__(self) -> int:
        return len(self.documents)

    def __repr__(self) -> str:
        return (f"BM25Index(count={len(self)}, k1={self.k1}, b={self.b}, "
                f"index_built={self._index_built})")
