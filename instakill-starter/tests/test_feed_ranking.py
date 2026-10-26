from copy import deepcopy
from datetime import datetime, timezone

from app.feed.ranking import FeedSignals, rank_feed

NOW = datetime(2026, 1, 10, tzinfo=timezone.utc)
WEIGHTS = {"freshness": 1.0, "affinity": 2.0, "popularity": 1.0}


def test_rank_feed_orders_by_score_and_breaks_ties_by_post_id():
    candidates = [
        {"post_id": 9, "user_id": 2, "content": "tie", "created_at": NOW},
        {"post_id": 4, "user_id": 2, "content": "tie", "created_at": NOW},
        {"post_id": 1, "user_id": 3, "content": "best", "created_at": NOW},
    ]
    signals = FeedSignals(
        followed_user_ids=frozenset({3}),
        author_like_counts={},
        post_like_counts={},
    )

    ranked = rank_feed(candidates, signals, NOW, WEIGHTS, 3)

    assert [post["post_id"] for post in ranked] == [1, 4, 9]
    assert all(isinstance(post["score"], float) for post in ranked)


def test_rank_feed_is_deterministic_and_does_not_mutate_inputs():
    candidates = [
        {"post_id": 8, "user_id": 2, "content": "older", "created_at": "2026-01-03T00:00:00"},
        {"post_id": 3, "user_id": 2, "content": "newer", "created_at": "2026-01-09T00:00:00"},
    ]
    signals = FeedSignals(
        followed_user_ids=frozenset({2}),
        author_like_counts={2: 1},
        post_like_counts={8: 2, 3: 1},
    )
    candidates_before = deepcopy(candidates)
    signals_before = deepcopy(signals)

    first = rank_feed(candidates, signals, NOW, WEIGHTS, 2)
    second = rank_feed(candidates, signals, NOW, WEIGHTS, 2)

    assert first == second
    assert candidates == candidates_before
    assert signals == signals_before
    assert all("score" not in post for post in candidates)


def test_rank_feed_returns_at_most_limit_results():
    candidates = [
        {"post_id": post_id, "user_id": 2, "content": "post", "created_at": NOW}
        for post_id in range(1, 5)
    ]
    signals = FeedSignals(frozenset(), {}, {})

    assert len(rank_feed(candidates, signals, NOW, WEIGHTS, 2)) == 2
