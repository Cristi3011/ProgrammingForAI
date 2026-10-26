"""SQLite reads required to build a user's feed."""
from app.db.database import get_connection


class FeedRepository:
    """Loads users, candidate posts, follows, and likes from SQLite."""

    def get_feed_data(self, user_id: int) -> dict | None:
        with get_connection() as conn:
            user = conn.execute("SELECT id FROM user WHERE id = ?", (user_id,)).fetchone()
            if user is None:
                return None

            posts = conn.execute(
                """
                SELECT id AS post_id, user_id, content, created_at
                FROM post
                ORDER BY id ASC
                """
            ).fetchall()
            follows = conn.execute(
                "SELECT followed_id FROM follow WHERE follower_id = ?",
                (user_id,),
            ).fetchall()
            likes = conn.execute(
                'SELECT user_id, post_id, created_at FROM "like"'
            ).fetchall()

        return {
            "posts": [dict(row) for row in posts],
            "followed_user_ids": [int(row["followed_id"]) for row in follows],
            "likes": [dict(row) for row in likes],
        }
