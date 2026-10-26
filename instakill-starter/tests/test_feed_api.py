import sqlite3

from fastapi.testclient import TestClient

from app.db import database
from app.main import app
from scripts.seed_db import seed


def test_feed_api_returns_ranked_posts_from_seeded_database(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "feed-test.db")
    seed()

    with TestClient(app) as client:
        with sqlite3.connect(database.DB_PATH) as conn:
            alice_id = conn.execute(
                "SELECT id FROM user WHERE username = 'alice'"
            ).fetchone()[0]
            liked_post_ids = {
                row[0]
                for row in conn.execute(
                    'SELECT post_id FROM "like" WHERE user_id = ?', (alice_id,)
                )
            }
        response = client.get("/feed", params={"user_id": alice_id})

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == alice_id
    assert body["strategy"] == "for_you"
    assert 0 < len(body["posts"]) <= 20
    assert all(
        {"post_id", "user_id", "content", "created_at", "score"} <= post.keys()
        for post in body["posts"]
    )
    assert all(post["user_id"] != alice_id for post in body["posts"])
    assert not liked_post_ids.intersection(
        post["post_id"] for post in body["posts"]
    )
    assert [post["score"] for post in body["posts"]] == sorted(
        (post["score"] for post in body["posts"]), reverse=True
    )


def test_feed_api_validates_parameters_and_unknown_user(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "feed-validation.db")
    seed()

    with TestClient(app) as client:
        assert client.get("/feed").status_code == 422
        assert client.get("/feed", params={"user_id": 1, "limit": 0}).status_code == 422
        assert client.get("/feed", params={"user_id": 1, "limit": 51}).status_code == 422
        assert client.get(
            "/feed", params={"user_id": 1, "strategy": "unknown"}
        ).status_code == 422
        assert client.get("/feed", params={"user_id": 99999}).status_code == 404
