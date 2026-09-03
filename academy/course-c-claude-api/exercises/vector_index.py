"""
VectorIndex — course scaffolding for the RAG block (003_vectordb.ipynb).

NOT a numbered exercise. An in-memory vector store the RAG lessons build
on (exercise 29 onward: the flow, BM25 comparison, multi-index pipeline).
Exercises import it:

    from vector_index import VectorIndex

WHAT IT IS
    Three parallel lists — vectors, documents, and nothing else. search()
    is brute force: distance from the query to EVERY stored vector, sort,
    take k. Fine for five chunks; real deployments swap this class for a
    vector database doing approximate nearest-neighbour, and nothing else
    in the pipeline changes — which is the point of learning it this way.

    distance_metric: "cosine" (default) or "euclidean". Cosine DISTANCE
    here = 1 - cosine similarity, so 0 = same direction, smaller = closer.

    Optionally construct with embedding_fn to let add_document(doc) and
    search("plain text") embed for themselves; without it, you pass
    vectors explicitly via add_vector (exercise 29 does the latter, so
    embedding stays visible in the exercise).

NOTEBOOK BUG, recorded — then fixed by the course itself: 003_vectordb's
demo cell calls store.add_documents([...]) which 003's class does not
define (AttributeError on the course's happy path). One notebook later,
005_hybrid.ipynb adds the method "to avoid rate limiting errors from
VoyageAI" — batch-embedding all contents in one call. This module carries
the fixed version.
"""

import math
from typing import Any, Dict, List, Optional, Tuple


class VectorIndex:
    def __init__(self, distance_metric: str = "cosine", embedding_fn=None):
        self.vectors: List[List[float]] = []
        self.documents: List[Dict[str, Any]] = []
        self._vector_dim: Optional[int] = None
        if distance_metric not in ["cosine", "euclidean"]:
            raise ValueError("distance_metric must be 'cosine' or 'euclidean'")
        self._distance_metric = distance_metric
        self._embedding_fn = embedding_fn

    def add_document(self, document: Dict[str, Any]):
        if not self._embedding_fn:
            raise ValueError("Embedding function not provided during initialization.")
        if not isinstance(document, dict):
            raise TypeError("Document must be a dictionary.")
        if "content" not in document:
            raise ValueError("Document dictionary must contain a 'content' key.")

        content = document["content"]
        if not isinstance(content, str):
            raise TypeError("Document 'content' must be a string.")

        vector = self._embedding_fn(content)
        self.add_vector(vector=vector, document=document)

    def add_documents(self, documents: List[Dict[str, Any]]):
        """Batch add: embed every content in ONE embedding call (the 005
        notebook's rate-limit fix), then store pairwise."""
        if not self._embedding_fn:
            raise ValueError("Embedding function not provided during initialization.")
        if not isinstance(documents, list):
            raise TypeError("Documents must be a list of dictionaries.")
        if not documents:
            return

        contents = []
        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                raise TypeError(f"Document at index {i} must be a dictionary.")
            if "content" not in doc:
                raise ValueError(f"Document at index {i} must contain a 'content' key.")
            if not isinstance(doc["content"], str):
                raise TypeError(f"Document 'content' at index {i} must be a string.")
            contents.append(doc["content"])

        vectors = self._embedding_fn(contents)

        for vector, document in zip(vectors, documents):
            self.add_vector(vector=vector, document=document)

    def add_vector(self, vector, document: Dict[str, Any]):
        if not isinstance(vector, list) or not all(
            isinstance(x, (int, float)) for x in vector
        ):
            raise TypeError("Vector must be a list of numbers.")
        if not isinstance(document, dict):
            raise TypeError("Document must be a dictionary.")
        if "content" not in document:
            raise ValueError("Document dictionary must contain a 'content' key.")

        if not self.vectors:
            self._vector_dim = len(vector)
        elif len(vector) != self._vector_dim:
            raise ValueError(
                f"Inconsistent vector dimension. Expected {self._vector_dim}, "
                f"got {len(vector)}")

        self.vectors.append(list(vector))
        self.documents.append(document)

    def search(self, query: Any, k: int = 1) -> List[Tuple[Dict[str, Any], float]]:
        if not self.vectors:
            return []

        if isinstance(query, str):
            if not self._embedding_fn:
                raise ValueError("Embedding function not provided for string query.")
            query_vector = self._embedding_fn(query)
        elif isinstance(query, list) and all(
            isinstance(x, (int, float)) for x in query
        ):
            query_vector = query
        else:
            raise TypeError("Query must be either a string or a list of numbers.")

        if self._vector_dim is None:
            return []

        if len(query_vector) != self._vector_dim:
            raise ValueError(
                f"Query vector dimension mismatch. Expected {self._vector_dim}, "
                f"got {len(query_vector)}")

        if k <= 0:
            raise ValueError("k must be a positive integer.")

        dist_func = (self._cosine_distance if self._distance_metric == "cosine"
                     else self._euclidean_distance)

        distances = [(dist_func(query_vector, stored), self.documents[i])
                     for i, stored in enumerate(self.vectors)]
        distances.sort(key=lambda item: item[0])

        return [(doc, dist) for dist, doc in distances[:k]]

    def _euclidean_distance(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimension")
        return math.sqrt(sum((p - q) ** 2 for p, q in zip(vec1, vec2)))

    def _dot_product(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimension")
        return sum(p * q for p, q in zip(vec1, vec2))

    def _magnitude(self, vec: List[float]) -> float:
        return math.sqrt(sum(x * x for x in vec))

    def _cosine_distance(self, vec1: List[float], vec2: List[float]) -> float:
        if len(vec1) != len(vec2):
            raise ValueError("Vectors must have the same dimension")

        mag1 = self._magnitude(vec1)
        mag2 = self._magnitude(vec2)

        if mag1 == 0 and mag2 == 0:
            return 0.0
        elif mag1 == 0 or mag2 == 0:
            return 1.0

        cosine_similarity = self._dot_product(vec1, vec2) / (mag1 * mag2)
        cosine_similarity = max(-1.0, min(1.0, cosine_similarity))

        return 1.0 - cosine_similarity

    def __len__(self) -> int:
        return len(self.vectors)

    def __repr__(self) -> str:
        has_embed_fn = "Yes" if self._embedding_fn else "No"
        return (f"VectorIndex(count={len(self)}, dim={self._vector_dim}, "
                f"metric='{self._distance_metric}', "
                f"has_embedding_fn='{has_embed_fn}')")
