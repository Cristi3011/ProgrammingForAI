from fastapi.testclient import TestClient

from app.api.search import get_search_service
from app.main import app


class FakeSearchService:
    def search(self, query: str, limit: int) -> dict:
        return {
            "query": query,
            "results": [
                {
                    "post_id": 2,
                    "user_id": 1,
                    "content": "A sample post",
                    "score": 0.75,
                }
            ][:limit],
        }


app.dependency_overrides[get_search_service] = lambda: FakeSearchService()


def test_search_success():
    with TestClient(app) as client:
        response = client.get("/search", params={"q": "sample", "limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "sample"
    assert body["results"][0]["post_id"] == 2
    assert body["results"][0]["user_id"] == 1
    assert body["results"][0]["content"] == "A sample post"
    assert isinstance(body["results"][0]["score"], (int, float))


def test_search_rejects_missing_query():
    with TestClient(app) as client:
        response = client.get("/search", params={"limit": 5})
    assert response.status_code == 422


def test_search_rejects_empty_query():
    with TestClient(app) as client:
        response = client.get("/search", params={"q": "  ", "limit": 5})
    assert response.status_code == 422


def test_search_rejects_missing_limit():
    with TestClient(app) as client:
        response = client.get("/search", params={"q": "sample"})
    assert response.status_code == 422


def test_search_rejects_out_of_range_limit():
    with TestClient(app) as client:
        for limit in (0, 21):
            response = client.get("/search", params={"q": "sample", "limit": limit})
            assert response.status_code == 422


def teardown_module():
    app.dependency_overrides.clear()