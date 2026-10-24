"""Application service coordinating repository reads, encoding, and retrieval."""
from __future__ import annotations

from threading import Lock

import numpy as np

from app.repositories.post_repository import PostRepository
from app.search.encoder import SentenceTransformerEncoder
from app.search.retrieval import retrieve_top_k


class SearchService:
    """Semantic search service with a small in-memory corpus index.

    The post corpus and its embeddings are cached on first search. Model loading
    and encoding are delegated to the encoder adapter.
    """

    def __init__(
        self,
        repository: PostRepository | None = None,
        encoder: SentenceTransformerEncoder | None = None,
    ) -> None:
        self.repository = repository or PostRepository()
        self.encoder = encoder or SentenceTransformerEncoder()
        self._posts: list[dict] | None = None
        self._corpus_vectors: np.ndarray | None = None
        self._index_lock = Lock()

    def _ensure_index(self) -> None:
        if self._posts is not None and self._corpus_vectors is not None:
            return
        with self._index_lock:
            if self._posts is not None and self._corpus_vectors is not None:
                return
            posts = self.repository.list_searchable_posts()
            if not posts:
                self._posts = []
                self._corpus_vectors = np.empty((0, 0), dtype=np.float32)
                return
            vectors = self.encoder.encode([post["content"] for post in posts])
            if vectors.ndim != 2 or vectors.shape[0] != len(posts):
                raise RuntimeError("Encoder returned an invalid corpus embedding matrix")
            self._posts = posts
            self._corpus_vectors = vectors

    def search(self, query: str, limit: int = 10) -> dict:
        """Search indexed posts and return a JSON-serializable response."""
        self._ensure_index()
        assert self._posts is not None
        assert self._corpus_vectors is not None

        if not self._posts:
            return {"query": query, "results": []}

        query_vector = self.encoder.encode([query])[0]
        results = retrieve_top_k(query_vector, self._posts, self._corpus_vectors, limit)
        return {"query": query, "results": results}

    def refresh_index(self) -> None:
        """Refresh cached posts/embeddings after the database receives new posts."""
        with self._index_lock:
            self._posts = None
            self._corpus_vectors = None
        self._ensure_index()