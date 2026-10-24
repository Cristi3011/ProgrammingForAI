"""Pure NumPy retrieval functions: no HTTP, database, or model loading."""
from __future__ import annotations

import numpy as np


def cosine_similarity(query_vector: np.ndarray, corpus_vectors: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between one query vector and every corpus row.

    Zero vectors receive score 0.0. Returns a 1-D float array.
    """
    query = np.asarray(query_vector, dtype=np.float64).reshape(-1)
    corpus = np.asarray(corpus_vectors, dtype=np.float64)

    if corpus.ndim != 2:
        raise ValueError("corpus_vectors must be a 2D matrix")
    if corpus.shape[1] != query.size:
        raise ValueError("query and corpus vectors must have the same dimension")

    query_norm = np.linalg.norm(query)
    row_norms = np.linalg.norm(corpus, axis=1)
    denominators = row_norms * query_norm
    scores = np.zeros(corpus.shape[0], dtype=np.float64)
    valid = denominators > 0
    if np.any(valid):
        scores[valid] = (corpus[valid] @ query) / denominators[valid]
    return np.clip(scores, -1.0, 1.0)


def top_k_indices(scores: np.ndarray, post_ids: np.ndarray, limit: int) -> np.ndarray:
    """Order indices by score descending and post_id ascending for ties."""
    scores = np.asarray(scores)
    post_ids = np.asarray(post_ids)

    if scores.ndim != 1 or post_ids.ndim != 1:
        raise ValueError("scores and post_ids must be one-dimensional")
    if len(scores) != len(post_ids):
        raise ValueError("scores and post_ids must have equal lengths")
    if not isinstance(limit, (int, np.integer)) or isinstance(limit, (bool, np.bool_)):
        raise ValueError("limit must be an integer")
    if limit < 0:
        raise ValueError("limit must be non-negative")
    if not np.all(np.isfinite(scores)):
        raise ValueError("scores must be finite")

    order = np.lexsort((post_ids, -scores))
    return order[: min(limit, len(order))]


def retrieve_top_k(
    query_vector: np.ndarray,
    posts: list[dict],
    corpus_vectors: np.ndarray,
    limit: int,
) -> list[dict]:
    """Return up to `limit` posts with their numeric cosine similarity score."""
    corpus = np.asarray(corpus_vectors)
    if len(posts) != len(corpus):
        raise ValueError("there must be one embedding row per post")

    scores = cosine_similarity(query_vector, corpus)
    post_ids = np.asarray([post["post_id"] for post in posts], dtype=np.int64)
    indices = top_k_indices(scores, post_ids, limit)

    results = []
    for index in indices:
        result = dict(posts[int(index)])
        result["score"] = float(scores[int(index)])
        results.append(result)
    return results