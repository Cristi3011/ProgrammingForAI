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