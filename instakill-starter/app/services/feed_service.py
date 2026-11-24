"""Feed orchestration: repository reads, signal preparation, and ranking."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
import math
from typing import Mapping

import numpy as np

from app.feed.ranking import FeedSignals, rank_feed
from app.feed.learned import LearnedScorer
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
        self.learned_scorer = LearnedScorer()

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
        lifetime_post_like_counts: Counter[int] = Counter()
        learned_popularity_counts: Counter[int] = Counter()
        post_authors = {
            int(post["post_id"]): int(post["user_id"]) for post in data["posts"]
        }
        cutoff = moment - POPULARITY_WINDOW
        learned_cutoff = moment - timedelta(
            days=self.learned_scorer.popularity_days
        )
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
            if created_at >= learned_cutoff:
                learned_popularity_counts[int(like["post_id"])] += 1
            lifetime_post_like_counts[int(like["post_id"])] += 1

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
        elif strategy == "learned":
            max_author_likes = max(author_like_counts.values(), default=0)
            max_post_likes = max(lifetime_post_like_counts.values(), default=1)
            max_learned_recent = max(
                learned_popularity_counts.values(), default=1
            )
            user_activity = len(liked_post_ids)
            rows = []
            for post in candidates:
                post_id = int(post["post_id"])
                author_id = int(post["user_id"])
                age_days = max(
                    0.0,
                    (moment - _parse_datetime(post["created_at"])).total_seconds()
                    / 86400.0,
                )
                author_likes = author_like_counts.get(author_id, 0)
                affinity = (
                    0.7 * float(author_id in set(data["followed_user_ids"]))
                    + 0.3 * (author_likes / max_author_likes if max_author_likes else 0.0)
                )
                activity = min(
                    1.0,
                    math.log1p(user_activity)
                    / math.log1p(self.learned_scorer.activity_cap),
                )
                lifetime = (
                    math.log1p(lifetime_post_like_counts[post_id])
                    / math.log1p(max_post_likes)
                )
                rows.append([
                    0.5 ** (
                        age_days / self.learned_scorer.half_life_days
                    ),
                    affinity,
                    learned_popularity_counts[post_id] / max_learned_recent,
                    activity,
                    lifetime,
                    min(
                        1.0,
                        age_days / self.learned_scorer.age_cap_days,
                    ),
                ])
            if not rows:
                posts = []
            else:
                scores = self.learned_scorer.predict(
                    np.asarray(rows, dtype=float)
                )
                ranked = sorted(
                    zip(candidates, scores),
                    key=lambda pair: (-float(pair[1]), int(pair[0]["post_id"])),
                )[:limit]
                posts = []
                for post, score in ranked:
                    item = dict(post)
                    item["score"] = float(score)
                    posts.append(item)
        else:
            signals = FeedSignals(
                followed_user_ids=frozenset(data["followed_user_ids"]),
                author_like_counts=author_like_counts,
                post_like_counts=post_like_counts,
            )
            posts = rank_feed(candidates, signals, moment, DEFAULT_WEIGHTS, limit)

        return {"user_id": user_id, "strategy": strategy, "posts": posts}
