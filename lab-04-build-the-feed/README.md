# Week 4 — Algorithms for AI: Build the Feed

This directory is the complete Week 4 package to post on Classroom.

## What must be delivered before the next lecture

1. **Lab challenge**: [`lab-04-build-the-feed/`](./lab-04-build-the-feed/) — read a guided, fully implemented feed ranker (freshness, affinity, and popularity signals, heap-based top-*k*, complexity measurements), tune its three weights so it beats the default weights and the chronological and popularity baselines on held-out data, and complete the `RESULTS` block.
2. **InstaKill**: extend the team repository from Weeks 1–3 with a working `GET /feed` endpoint (details below). Create a demonstrable commit/tag.

## Required resources

- Python 3.11+
- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html)
- [MovieLens datasets](https://grouplens.org/datasets/movielens/) (`latest-small`)
- [NumPy quickstart](https://numpy.org/doc/stable/user/quickstart.html)

## Compute policy

The lab must run on CPU with the standard library and NumPy only; a GPU is not required. It uses MovieLens `latest-small` (about 1 MB): download the zip in your browser from the GroupLens link above and upload it to the notebook when asked — an automatic download from Python fails on GroupLens's certificate chain. Do not commit the data. Do not use a hosted service or a paid API.

## InstaKill requirement

Work in the repository your team started in Week 1. Keep the Pydantic `User` and `Post` models, the Week 2 service boundary, and the Week 3 `GET /search` code. The Week 2 lab ranker (`2 * likes + comments - age_hours`) was a lab-only exercise; you may start from it, but your feed's weights must be your own and justified.

Implement this endpoint:

```text
GET /feed?user_id=<int>&limit=<1..50>&strategy=for_you|chronological
```

A successful response returns the `user_id`, the `strategy`, and a list of up to `limit` posts. Each post contains at least `post_id`, `user_id` (author), `content`, and `created_at`; `for_you` results also contain a numeric `score`. `for_you` results are ordered by descending score and `chronological` results by newest `created_at`; in both cases equal values use ascending `post_id` as the deterministic tie-breaker. An unknown `user_id` returns 404; a missing `user_id`, an out-of-range `limit`, or an unknown `strategy` returns a clear client error (default `strategy` is `for_you`, default `limit` is 20).

What to add:

- **Data:** `follow` and `like` tables created by your existing database bootstrap, plus an extension of `scripts/seed_db.py` with enough seeded follows and likes to produce non-trivial feeds. Do **not** add endpoints that create users, posts, follows, or likes — that CRUD work is Week 5.
- **Pure ranking function:** `rank_feed(candidates, signals, now, weights, limit)` returns the ordered top results using a heap-based top-*k*. It receives `now` as an argument (never calls the clock), performs no I/O, and does not mutate its inputs.
- **Boundaries:** database reads behind a repository, orchestration in your service module, and HTTP parsing/response formatting at the API edge.
- **Candidates and cold start:** exclude the user's own posts and posts the user already liked. Document which posts are candidates (for example, followed authors) and what a user who follows nobody sees.
- **Signals:** at least three, such as freshness, affinity to followed authors or liked content, and popularity. Document the formula and the default weights.
- **Tests:** `pytest` tests for `rank_feed` (ordering, tie-break, determinism, input not mutated) and one API test over the seeded database. Keep them runnable with a single command.
- **Complexity note:** in the README, state the Big-O of one `GET /feed` request in terms of the number of candidates *C* and the limit *k*, and say which part you would precompute first.
- **Contract:** update `docs/api-contract.md` with the implemented endpoint.

Do not use machine-learning models, embeddings, or the Week 3 search code in the feed, and do not evaluate it formally yet — the evaluation protocol comes in Week 7. The `chronological` strategy exists so that baseline comparison is possible then.

## Structure

```text
assignment/
├── README.md
└── lab-04-build-the-feed/
    ├── README.md
    └── week04.ipynb
```
