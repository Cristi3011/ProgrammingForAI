"""SQLite repository for reading posts used by semantic search."""
from app.db.database import get_connection


class PostRepository:
    """Reads post records without exposing SQLite details to search logic."""

    def list_searchable_posts(self) -> list[dict]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT id AS post_id, user_id, content FROM post ORDER BY id ASC"
            ).fetchall()
        return [
            {
                "post_id": int(row["post_id"]),
                "user_id": int(row["user_id"]),
                "content": str(row["content"]),
            }
            for row in rows
        ]