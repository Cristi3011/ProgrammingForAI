"""Feed orchestration: repository reads, signal preparation, and ranking."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Mapping

from app.feed.ranking import FeedSignals, rank_feed
from app.repositories.feed_repository import FeedRepository

POPULARITY_WINDOW = timedelta(days=30)
DEFAULT_WEIGHTS = {"freshness": 1.0, "affinity": 2.0, "popularity": 1.0}


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class FeedService:
    """Builds ranked or chronological feeds for existing users."""

    def __init__(self, repository: FeedRepository | None = None) -> None:
        self.repository = repository or FeedRepository()

    def get_feed(
        self,
        user_id: int,
        limit: int = 20,
        strategy: str = "for_you",
        now: datetime | None = None,
    ) -> dict | None:
        data = self.repository.get_feed_data(user_id)
        if data is None:
            return None

        moment = _parse_datetime(now or datetime.now(timezone.utc))
        liked_post_ids = set()
        author_like_counts: Counter[int] = Counter()
        post_like_counts: Counter[int] = Counter()
        post_authors = {
            int(post["post_id"]): int(post["user_id"]) for post in data["posts"]
        }
        cutoff = moment - POPULARITY_WINDOW
        for like in data["likes"]:
            created_at = _parse_datetime(like["created_at"])
            if created_at > moment:
                continue
            if int(like["user_id"]) == user_id:
                post_id = int(like["post_id"])
                liked_post_ids.add(post_id)
                post_author = post_authors.get(post_id)
                if post_author is not None:
                    author_like_counts[post_author] += 1
            if created_at >= cutoff:
                post_like_counts[int(like["post_id"])] += 1

        candidates = [
            post
            for post in data["posts"]
            if int(post["user_id"]) != user_id
            and int(post["post_id"]) not in liked_post_ids
            and _parse_datetime(post["created_at"]) <= moment
        ]

        if strategy == "chronological":
            posts = sorted(
                candidates,
                key=lambda post: (
                    -_parse_datetime(post["created_at"]).timestamp(),
                    int(post["post_id"]),
                ),
            )[:limit]
        else:
            signals = FeedSignals(
                followed_user_ids=frozenset(data["followed_user_ids"]),
                author_like_counts=author_like_counts,
                post_like_counts=post_like_counts,
            )
            posts = rank_feed(candidates, signals, moment, DEFAULT_WEIGHTS, limit)

        return {"user_id": user_id, "strategy": strategy, "posts": posts}
