import numpy as np

from app.services.search_service import SearchService


class FakeRepository:
    def __init__(self):
        self.calls = 0

    def list_searchable_posts(self):
        self.calls += 1
        return [
            {"post_id": 5, "user_id": 2, "content": "first post"},
            {"post_id": 2, "user_id": 1, "content": "second post"},
        ]


class FakeEncoder:
    def __init__(self):
        self.calls = []

    def encode(self, texts):
        self.calls.append(list(texts))
        vectors = {
            "first post": [1.0, 0.0],
            "second post": [1.0, 0.0],
            "query": [1.0, 0.0],
        }
        return np.asarray([vectors[text] for text in texts], dtype=np.float32)


def test_search_service_returns_results_and_caches_corpus():
    repository = FakeRepository()
    encoder = FakeEncoder()
    service = SearchService(repository=repository, encoder=encoder)

    response = service.search("query", 2)

    assert response["query"] == "query"
    assert [item["post_id"] for item in response["results"]] == [2, 5]
    assert all(isinstance(item["score"], float) for item in response["results"])
    assert repository.calls == 1
    assert encoder.calls == [["first post", "second post"], ["query"]]

    service.search("query", 1)
    assert repository.calls == 1
    assert encoder.calls[-1] == ["query"]


def test_refresh_index_reads_posts_again():
    repository = FakeRepository()
    encoder = FakeEncoder()
    service = SearchService(repository=repository, encoder=encoder)

    service.search("query", 1)
    service.refresh_index()

    assert repository.calls == 2