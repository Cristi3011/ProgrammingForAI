"""Seeds the InstaKill database with users, posts, follows, and likes."""
from datetime import datetime, timedelta, timezone

from app.db.database import get_connection, init_db

USERS = ["alice", "bob", "carol", "dave", "erin"]
POSTS = [
    ("alice", "hello world, this is my first post"),
    ("alice", "does anyone else think the feed is chronological only? boring"),
    ("bob", "just shipped a cosine similarity search, feels great"),
    ("carol", "spam spam spam buy now click here"),
    ("dave", "benchmarking my ranker against popularity baseline today"),
    ("erin", "red-team week is going to be brutal, good luck everyone"),
    ("bob", "I am learning Python and building an API this week"),
    ("bob", "A new day for testing my backend project"),
    ("carol", "Trying a fresh approach to software design"),
    ("carol", "Weekend plans: coffee, books, and a little coding"),
    ("dave", "Working on a recommender system with a simple ranking formula"),
    ("dave", "Small improvements make a big difference in performance"),
    ("erin", "Exploring machine learning ideas with my study group"),
    ("erin", "What is everyone building for the course project?"),
    ("alice", "Sharing notes about reliable database migrations"),
]
FOLLOWS = [
    ("alice", "bob"),
    ("alice", "dave"),
    ("bob", "alice"),
    ("bob", "carol"),
    ("carol", "bob"),
    ("carol", "erin"),
    ("dave", "alice"),
    ("dave", "erin"),
    ("erin", "carol"),
    ("erin", "dave"),
]
LIKES = [
    ("alice", "just shipped a cosine similarity search, feels great"),
    ("alice", "benchmarking my ranker against popularity baseline today"),
    ("bob", "hello world, this is my first post"),
    ("bob", "Trying a fresh approach to software design"),
    ("carol", "I am learning Python and building an API this week"),
    ("carol", "Exploring machine learning ideas with my study group"),
    ("dave", "Weekend plans: coffee, books, and a little coding"),
    ("dave", "does anyone else think the feed is chronological only? boring"),
    ("erin", "Working on a recommender system with a simple ranking formula"),
    ("erin", "Small improvements make a big difference in performance"),
    ("alice", "Trying a fresh approach to software design"),
    ("alice", "Exploring machine learning ideas with my study group"),
    ("alice", "Weekend plans: coffee, books, and a little coding"),
    ("alice", "Working on a recommender system with a simple ranking formula"),
    ("bob", "does anyone else think the feed is chronological only? boring"),
    ("bob", "benchmarking my ranker against popularity baseline today"),
    ("bob", "red-team week is going to be brutal, good luck everyone"),
    ("bob", "Sharing notes about reliable database migrations"),
    ("carol", "hello world, this is my first post"),
    ("carol", "benchmarking my ranker against popularity baseline today"),
    ("carol", "A new day for testing my backend project"),
    ("carol", "Small improvements make a big difference in performance"),
    ("dave", "I am learning Python and building an API this week"),
    ("dave", "Trying a fresh approach to software design"),
    ("dave", "Exploring machine learning ideas with my study group"),
    ("dave", "What is everyone building for the course project?"),
    ("erin", "hello world, this is my first post"),
    ("erin", "just shipped a cosine similarity search, feels great"),
    ("erin", "Trying a fresh approach to software design"),
    ("erin", "red-team week is going to be brutal, good luck everyone"),
]


def seed() -> None:
    init_db()
    with get_connection() as conn:
        for username in USERS:
            conn.execute(
                "INSERT OR IGNORE INTO user (username) VALUES (?)", (username,)
            )
        user_ids = {
            row["username"]: int(row["id"])
            for row in conn.execute("SELECT id, username FROM user")
        }
        for index, (username, content) in enumerate(POSTS):
            user_id = user_ids[username]
            exists = conn.execute(
                "SELECT 1 FROM post WHERE user_id = ? AND content = ?",
                (user_id, content),
            ).fetchone()
            if exists is None:
                conn.execute(
                    "INSERT INTO post (user_id, content, created_at) "
                    "VALUES (?, ?, ?)",
                    (
                        user_id,
                        content,
                        (
                            datetime(2026, 8, 1, tzinfo=timezone.utc)
                            + timedelta(days=index * 3)
                        ).isoformat(),
                    ),
                )
            else:
                conn.execute(
                    "UPDATE post SET created_at = ? "
                    "WHERE user_id = ? AND content = ?",
                    (
                        (
                            datetime(2026, 8, 1, tzinfo=timezone.utc)
                            + timedelta(days=index * 3)
                        ).isoformat(),
                        user_id,
                        content,
                    ),
                )
        post_ids = {
            row["content"]: int(row["id"])
            for row in conn.execute("SELECT id, content FROM post")
        }
        for follower, followed in FOLLOWS:
            conn.execute(
                "INSERT OR IGNORE INTO follow (follower_id, followed_id) VALUES (?, ?)",
                (user_ids[follower], user_ids[followed]),
            )
        for index, (liker, content) in enumerate(LIKES):
            liked_at = (
                datetime(2026, 9, 1, tzinfo=timezone.utc)
                + timedelta(days=(index % 30))
            ).isoformat()
            conn.execute(
                'INSERT OR IGNORE INTO "like" '
                "(user_id, post_id, created_at) VALUES (?, ?, ?)",
                (user_ids[liker], post_ids[content], liked_at),
            )
            conn.execute(
                'UPDATE "like" SET created_at = ? '
                "WHERE user_id = ? AND post_id = ?",
                (liked_at, user_ids[liker], post_ids[content]),
            )
        conn.commit()
    print(
        f"Seeded {len(USERS)} users, {len(POSTS)} posts, "
        f"{len(FOLLOWS)} follows, and {len(LIKES)} likes."
    )


if __name__ == "__main__":
    seed()
