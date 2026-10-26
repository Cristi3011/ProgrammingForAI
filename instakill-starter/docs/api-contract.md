# API Contract — Create User

**Endpoint:** `POST /users`

**Status:** Planned — not implemented in this milestone.

## 1. Request

Content-Type: `application/json`

The client sends a JSON object containing the username.

```json
{
  "username": "alex"
}
```

The `username` field is required and must not be empty or contain only whitespace.

## 2. Successful Response

**Status:** `201 Created`

```json
{
  "id": 1,
  "username": "alex",
  "created_at": "2026-10-22T12:00:00"
}
```

The response represents the created user. The `id` is assigned when the user is persisted, and `created_at` is the creation timestamp.

## 3. Validation and Error Cases

- `422 Unprocessable Entity`: the request body is invalid, the username is missing, or the username is empty.
- `500 Internal Server Error`: an unexpected server-side error occurs.

These responses describe the planned contract only. The endpoint is not implemented in this milestone.

---

# API Contract — Feed

**Endpoint:** `GET /feed`

## 1. Request

Query parameters:

| Parameter | Required | Default | Constraints |
|---|---:|---:|---|
| `user_id` | Yes | — | Integer ID of an existing user |
| `limit` | No | `20` | Integer from 1 through 50 |
| `strategy` | No | `for_you` | `for_you` or `chronological` |

## 2. Successful Response

**Status:** `200 OK`

```json
{
  "user_id": 1,
  "strategy": "for_you",
  "posts": [
    {
      "post_id": 12,
      "user_id": 2,
      "content": "A sample post",
      "created_at": "2026-10-26T18:00:00",
      "score": 2.43
    }
  ]
}
```

`posts` contains up to `limit` candidates. The requesting user's own posts and posts they have already liked are excluded. `for_you` orders by descending score and includes a numeric `score`; `chronological` orders by newest `created_at`. Equal scores or timestamps are ordered by ascending `post_id`.

Candidates may be authored by any user, so a user with no follows or likes still receives recent and popular public posts. The `for_you` score is the weighted sum of freshness (`0.5 ** (age_days / 7)`), author affinity (followed-author signal plus the user's prior likes of that author's posts), and recent popularity (likes over the last 30 days, normalized by the most-liked post). Default weights are `1.0`, `2.0`, and `1.0`, respectively.

## 3. Validation and Error Cases

- `404 Not Found`: `user_id` does not identify an existing user.
- `422 Unprocessable Entity`: `user_id` is missing or invalid, `limit` is outside 1–50, or `strategy` is not supported.