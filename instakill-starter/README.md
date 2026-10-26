# InstaKill — Starter Repo

Mini social-media platform. Mandatory backend: Python + FastAPI + SQLite (default) / PostgreSQL (allowed). See the full brief and grading rubric in `masterplan.md` (course root).

What the instructor provides (this starter):

- `app/main.py` — FastAPI hello-world with `GET /health`
- `app/db/database.py` — SQLite bootstrap (creates tables on startup)
- `app/domain/models.py` — `User` / `Post` schema
- `scripts/seed_db.py` — 5-10 synthetic users/posts
- `tests/test_health.py` — test skeleton

What it does **not** provide: ranking and the feed. Those are the team's work in Week 4. Semantic search is implemented separately for Week 3.

## Running it

```bash
pip install -e .
uvicorn app.main:app --reload
# other terminal:
curl localhost:8000/health

python scripts/seed_db.py
pytest
```

## Milestones (see masterplan.md for full details)

W1 Repo+API → W3 CRUD+DB → W4 Feed v0 → W7 Baseline+eval plan → W9 ML+pretrained feature → W11 Profile+optimize → W13 Feature freeze+E2E → W14 Red-team+Demo Day.

At the end of each week: a demonstrable commit/tag.

## Week 4 — Feed

`GET /feed?user_id=<int>&limit=<1..50>&strategy=for_you|chronological` returns at most 20 posts by default (`limit` maximum 50). `for_you` combines:

- freshness: `0.5 ** (age_days / 7)`;
- affinity: `0.7` for a followed author plus up to `0.3` for authors whose posts the user has liked before, normalized to the user's most-liked author;
- popularity: the post's likes from the last 30 days, normalized by the most-liked post.

Default weights are freshness `1.0`, affinity `2.0`, and popularity `1.0`. Candidates are posts from every author except the requesting user, posts already liked by that user, and posts created in the future. This allows cold-start users with no follows or likes to see recent and popular public posts. `chronological` orders the same candidates newest-first; both strategies break ties by ascending post ID.

The ranker scores `C` candidates and uses a heap to select `k` results in `O(C log k)` time and `O(k)` ranking memory. Preparing signals is `O(L)` for `L` likes. The first data worth precomputing at larger scale is recent popularity counts, since the same per-post counts are reused for every user request.

Feed tests run with `pytest` from this directory. The seed script is safe to rerun and creates sample follows and likes:

```bash
python scripts/seed_db.py
pytest
```
