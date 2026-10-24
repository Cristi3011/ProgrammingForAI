import numpy as np
import pytest

from app.search.retrieval import cosine_similarity, retrieve_top_k, top_k_indices


def test_cosine_similarity_known_values():
    scores = cosine_similarity(
        np.array([1.0, 0.0]),
        np.array([[1.0, 0.0], [0.0, 1.0], [-1.0, 0.0]]),
    )
    np.testing.assert_allclose(scores, [1.0, 0.0, -1.0])


def test_zero_vector_has_zero_similarity():
    scores = cosine_similarity(np.array([0.0, 0.0]), np.array([[1.0, 0.0]]))
    np.testing.assert_allclose(scores, [0.0])


def test_top_k_ties_are_broken_by_ascending_post_id():
    indices = top_k_indices(
        np.array([0.8, 0.9, 0.9, 0.7]),
        np.array([10, 8, 3, 1]),
        3,
    )
    assert indices.tolist() == [2, 1, 0]


def test_retrieve_returns_numeric_scores_and_expected_order():
    posts = [
        {"post_id": 7, "user_id": 1, "content": "A"},
        {"post_id": 2, "user_id": 2, "content": "B"},
    ]
    vectors = np.array([[1.0, 0.0], [1.0, 0.0]])
    results = retrieve_top_k(np.array([1.0, 0.0]), posts, vectors, 2)
    assert [result["post_id"] for result in results] == [2, 7]
    assert all(isinstance(result["score"], float) for result in results)


def test_top_k_rejects_negative_limit():
    with pytest.raises(ValueError):
        top_k_indices(np.array([0.5]), np.array([1]), -1)