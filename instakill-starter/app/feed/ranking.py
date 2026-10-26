"""Pure scoring and heap-based top-k ranking for the social feed."""
from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping, Sequence

HALF_LIFE_SECONDS = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class FeedSignals:
    """Precomputed interaction signals used to score candidate posts."""

    followed_user_ids: frozenset[int]
    author_like_counts: Mapping[int, int]
    post_like_counts: Mapping[int, int]


def _as_utc(value: datetime | str) -> datetime:
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def rank_feed(
    candidates: Sequence[dict],
    signals: FeedSignals,
    now: datetime,
    weights: Mapping[str, float],
    limit: int,
) -> list[dict]:
    """Return the highest-scoring candidates without mutating the inputs.

    Scores combine freshness (seven-day half-life), affinity (followed author
    plus the user's past likes of that author's posts), and recent popularity.
    """
    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 0:
        raise ValueError("limit must be a non-negative integer")
    required_weights = {"freshness", "affinity", "popularity"}
    if set(weights) != required_weights:
        raise ValueError("weights must define freshness, affinity, and popularity")
    if any(not math.isfinite(float(value)) or value < 0 for value in weights.values()):
        raise ValueError("weights must be finite and non-negative")
    if limit == 0 or not candidates:
        return []

    moment = _as_utc(now)
    max_author_likes = max(signals.author_like_counts.values(), default=0)
    max_post_likes = max(signals.post_like_counts.values(), default=0)

    def scored_posts():
        for candidate in candidates:
            created_at = _as_utc(candidate["created_at"])
            age_seconds = max(0.0, (moment - created_at).total_seconds())
            freshness = 0.5 ** (age_seconds / HALF_LIFE_SECONDS)

            author_id = int(candidate["user_id"])
            author_likes = signals.author_like_counts.get(author_id, 0)
            author_affinity = (
                author_likes / max_author_likes if max_author_likes else 0.0
            )
            affinity = (
                0.7 * float(author_id in signals.followed_user_ids)
                + 0.3 * author_affinity
            )

            post_id = int(candidate["post_id"])
            post_likes = signals.post_like_counts.get(post_id, 0)
            popularity = post_likes / max_post_likes if max_post_likes else 0.0

            score = (
                float(weights["freshness"]) * freshness
                + float(weights["affinity"]) * affinity
                + float(weights["popularity"]) * popularity
            )
            result = dict(candidate)
            result["score"] = float(score)
            yield score, post_id, result

    best = heapq.nsmallest(
        limit, scored_posts(), key=lambda item: (-item[0], item[1])
    )
    return [result for _, _, result in best]
