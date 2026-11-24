import sqlite3
from datetime import datetime, timezone

from scripts.evaluate import ndcg, snapshot, evaluate


def test_ndcg_at_10_cases():
    assert ndcg([1, 2, 3], set()) == 0.0
    assert ndcg([1, 2, 3], {1, 2, 3}) == 1.0
    ranking = [9, 8, 7, 4, 5, 6]
    assert 0.0 < ndcg(ranking, {7}) < 1.0


def test_snapshot_removes_future_likes_and_posts(tmp_path):
    db = tmp_path / "fixture.db"
    cutoff = datetime(2026, 10, 15, tzinfo=timezone.utc)
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE user (id INTEGER PRIMARY KEY);
            CREATE TABLE post (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                content TEXT,
                created_at TEXT
            );
            CREATE TABLE "like" (
                user_id INTEGER,
                post_id INTEGER,
                created_at TEXT
            );
            CREATE TABLE follow (
                follower_id INTEGER,
                followed_id INTEGER
            );
            INSERT INTO user VALUES (1);
            INSERT INTO user VALUES (2);
            INSERT INTO post VALUES
                (1, 1, 'before', '2026-10-01T00:00:00+00:00'),
                (2, 2, 'after', '2026-11-01T00:00:00+00:00');
            INSERT INTO "like" VALUES
                (1, 1, '2026-10-01T00:00:00+00:00'),
                (1, 1, '2026-11-01T00:00:00+00:00');
            """
        )

    snap = snapshot(db, cutoff)
    with sqlite3.connect(snap) as conn:
        assert conn.execute("SELECT COUNT(*) FROM post").fetchone()[0] == 1
        assert conn.execute('SELECT COUNT(*) FROM "like"').fetchone()[0] == 1
    snap.unlink()


def test_deterministic_csv(tmp_path, monkeypatch):
    db = tmp_path / "fixture.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE user (id INTEGER PRIMARY KEY);
            CREATE TABLE post (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                content TEXT,
                created_at TEXT
            );
            CREATE TABLE "like" (
                user_id INTEGER,
                post_id INTEGER,
                created_at TEXT
            );
            CREATE TABLE follow (
                follower_id INTEGER,
                followed_id INTEGER
            );
            INSERT INTO user VALUES (1);
            INSERT INTO user VALUES (2);
            INSERT INTO post VALUES
                (1, 2, 'before', '2026-08-01T00:00:00+00:00'),
                (2, 2, 'after', '2026-11-01T00:00:00+00:00');
            INSERT INTO "like" VALUES
                (1, 1, '2026-08-01T00:00:00+00:00'),
                (1, 1, '2026-09-01T00:00:00+00:00'),
                (1, 1, '2026-09-15T00:00:00+00:00'),
                (1, 1, '2026-11-01T00:00:00+00:00');
            """
        )

    cutoff = datetime(2026, 10, 1, tzinfo=timezone.utc)
    first = tmp_path / "first"
    second = tmp_path / "second"
    evaluate(db, cutoff, 42, first)
    evaluate(db, cutoff, 42, second)
    assert (first / "eval_results.csv").read_bytes() == (
        second / "eval_results.csv"
    ).read_bytes()


def test_evaluation_uses_feed_service(monkeypatch, tmp_path):
    from app.services.feed_service import FeedService

    calls = []
    original = FeedService.get_feed

    def counted(self, user_id, limit=20, strategy="for_you", now=None):
        calls.append((user_id, limit, strategy))
        return {"user_id": user_id, "strategy": strategy, "posts": []}

    monkeypatch.setattr(FeedService, "get_feed", counted)
    # Fixture exercise: one eligible user and one relevant later like.
    db = tmp_path / "fixture.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(
            """
            CREATE TABLE user (id INTEGER PRIMARY KEY);
            CREATE TABLE post (
                id INTEGER PRIMARY KEY, user_id INTEGER,
                content TEXT, created_at TEXT
            );
            CREATE TABLE "like" (
                user_id INTEGER, post_id INTEGER, created_at TEXT
            );
            CREATE TABLE follow (
                follower_id INTEGER, followed_id INTEGER
            );
            INSERT INTO user VALUES (1);
            INSERT INTO user VALUES (2);
            INSERT INTO post VALUES
                (1, 2, 'before', '2026-08-01T00:00:00+00:00'),
                (2, 2, 'after', '2026-11-01T00:00:00+00:00');
            INSERT INTO "like" VALUES
                (1, 1, '2026-08-01T00:00:00+00:00'),
                (1, 1, '2026-09-01T00:00:00+00:00'),
                (1, 1, '2026-09-15T00:00:00+00:00'),
                (1, 1, '2026-11-01T00:00:00+00:00');
            """
        )
    cutoff = datetime(2026, 10, 1, tzinfo=timezone.utc)
    evaluate(db, cutoff, 42, tmp_path / "reports")
    assert calls == [(1, 10, "chronological"),
                     (1, 10, "for_you"),
                     (1, 10, "learned")]
