"""Offline time-split evaluation for InstaKill."""
import argparse
import base64
import csv
import hashlib
import io
import math
import random
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.db import database
from app.services.feed_service import FeedService

STRATEGIES = ("chronological", "popularity", "for_you", "learned")
GROUPS = ("new", "casual", "regular", "power")


def time_value(value):
    result = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result.astimezone(timezone.utc)


def iso(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def ndcg(ranking, relevant):
    dcg = sum(
        1.0 / math.log2(i + 2)
        for i, post_id in enumerate(ranking[:10])
        if post_id in relevant
    )
    ideal = sum(1.0 / math.log2(i + 2) for i in range(min(len(relevant), 10)))
    return dcg / ideal if ideal else 0.0


def cutoff(db_path, supplied=None):
    if supplied:
        return time_value(supplied)
    with sqlite3.connect(db_path) as conn:
        times = [
            time_value(row[0])
            for row in conn.execute('SELECT created_at FROM "like"')
            if row[0]
        ]
    if not times:
        raise ValueError("Database has no likes")
    times.sort()
    position = (len(times) - 1) * 0.8
    low, high = math.floor(position), math.ceil(position)
    if low == high:
        return times[low]
    fraction = position - low
    return times[low] + (times[high] - times[low]) * fraction


def snapshot(db_path, cutoff_time):
    handle = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    handle.close()
    path = Path(handle.name)
    source = sqlite3.connect(db_path)
    dest = sqlite3.connect(path)
    source.backup(dest)
    source.close()

    with dest:
        for table in ("like", "post"):
            rows = dest.execute(
                f'SELECT rowid, created_at FROM "{table}"'
            ).fetchall()
            for rowid, created_at in rows:
                if created_at and time_value(created_at) >= cutoff_time:
                    dest.execute(
                        f'DELETE FROM "{table}" WHERE rowid = ?',
                        (rowid,),
                    )
    dest.close()
    return path


def user_group(count):
    if count < 10:
        return "new"
    if count < 50:
        return "casual"
    if count < 200:
        return "regular"
    return "power"


def eligible_users(db_path, snapshot_path, cutoff_time):
    with sqlite3.connect(snapshot_path) as conn:
        post_ids = {
            row[0] for row in conn.execute("SELECT id FROM post")
        }
        users = [
            row[0] for row in conn.execute("SELECT id FROM user")
        ]

    result = []
    with sqlite3.connect(db_path) as conn:
        for user_id in users:
            likes = conn.execute(
                'SELECT post_id, created_at FROM "like" WHERE user_id = ?',
                (user_id,),
            ).fetchall()
            before = [
                row for row in likes
                if row[1] and time_value(row[1]) < cutoff_time
            ]
            relevant = {
                row[0] for row in likes
                if row[1]
                and time_value(row[1]) >= cutoff_time
                and row[0] in post_ids
            }
            if len(before) >= 3 and relevant:
                result.append((user_id, relevant, user_group(len(before))))
    return sorted(result)


def popularity_ranking(path, user_id, cutoff_time):
    with sqlite3.connect(path) as conn:
        liked = {
            row[0] for row in conn.execute(
                'SELECT post_id FROM "like" WHERE user_id = ?', (user_id,)
            )
        }
        posts = conn.execute(
            "SELECT id FROM post WHERE user_id != ?", (user_id,)
        ).fetchall()
        counts = {}
        start = iso(cutoff_time - timedelta(days=30))
        end = iso(cutoff_time)
        for (post_id,) in posts:
            counts[post_id] = conn.execute(
                'SELECT COUNT(*) FROM "like" '
                "WHERE post_id = ? AND created_at >= ? AND created_at < ?",
                (post_id, start, end),
            ).fetchone()[0]
    candidates = [post_id for post_id in counts if post_id not in liked]
    return sorted(
        candidates,
        key=lambda post_id: (-counts[post_id], post_id),
    )[:10]


def bootstrap(values, seed):
    if not values:
        return 0.0, 0.0
    rng = random.Random(seed)
    means = []
    for _ in range(2000):
        sample = [values[rng.randrange(len(values))] for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    return means[50], means[1949]


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return "unknown"


def png_data(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", bbox_inches="tight", dpi=150)
    return "data:image/png;base64," + base64.b64encode(
        buffer.getvalue()
    ).decode("ascii")


def evaluate(db_path, cutoff_time, seed, out):
    snap = snapshot(db_path, cutoff_time)
    users = eligible_users(db_path, snap, cutoff_time)
    rows = []

    old_db = database.DB_PATH
    database.DB_PATH = snap
    service = FeedService()
    try:
        for user_id, relevant, group in users:
            rankings = {}
            for strategy in ("chronological", "for_you", "learned"):
                response = service.get_feed(
                    user_id, limit=10, strategy=strategy, now=cutoff_time
                )
                rankings[strategy] = [
                    post["post_id"] for post in response["posts"]
                ]
            rankings["popularity"] = popularity_ranking(
                snap, user_id, cutoff_time
            )
            for strategy in STRATEGIES:
                rows.append({
                    "user_id": user_id,
                    "strategy": strategy,
                    "ndcg_at_10": ndcg(rankings[strategy], relevant),
                    "n_relevant": len(relevant),
                    "user_group": group,
                })
    finally:
        database.DB_PATH = old_db
        snap.unlink(missing_ok=True)

    out.mkdir(parents=True, exist_ok=True)
    fields = ("user_id", "strategy", "ndcg_at_10", "n_relevant", "user_group")
    with (out / "eval_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in sorted(rows, key=lambda item: (item["user_id"], item["strategy"])):
            row = dict(row)
            row["ndcg_at_10"] = f'{row["ndcg_at_10"]:.6f}'
            writer.writerow(row)

    summary = {}
    for strategy in STRATEGIES:
        values = [
            row["ndcg_at_10"] for row in rows
            if row["strategy"] == strategy
        ]
        low, high = bootstrap(values, seed)
        mean = sum(values) / len(values) if values else 0.0
        summary[strategy] = (mean, low, high)

    lines = [
        "# Offline evaluation",
        "",
        "| Strategy | Mean NDCG@10 | 95% interval | Users |",
        "|---|---:|---:|---:|",
    ]
    for strategy in STRATEGIES:
        mean, low, high = summary[strategy]
        count = sum(row["strategy"] == strategy for row in rows)
        lines.append(
            f"| {strategy} | {mean:.6f} | [{low:.6f}, {high:.6f}] | {count} |"
        )

    lines += [
        "",
        "## Learned minus best baseline",
        "",
        "| Slice | Difference | 95% interval | Verdict |",
        "|---|---:|---:|---|",
    ]
    differences = {}
    slices = [("all", rows)] + [
        (group, [row for row in rows if row["user_group"] == group])
        for group in GROUPS
    ]
    for name, section in slices:
        if not section:
            continue
        by_user = sorted({row["user_id"] for row in section})
        means = {}
        for strategy in STRATEGIES:
            values = [
                row["ndcg_at_10"] for row in section
                if row["strategy"] == strategy
            ]
            means[strategy] = sum(values) / len(values)
        best = max(
            ("chronological", "popularity", "for_you"),
            key=lambda strategy: means[strategy],
        )
        learned = {
            row["user_id"]: row["ndcg_at_10"]
            for row in section if row["strategy"] == "learned"
        }
        baseline = {
            row["user_id"]: row["ndcg_at_10"]
            for row in section if row["strategy"] == best
        }
        paired = [
            learned[user_id] - baseline[user_id]
            for user_id in by_user
        ]
        difference = sum(paired) / len(paired)
        low, high = bootstrap(paired, seed)
        verdict = "wins" if low > 0 else "loses" if high < 0 else "unclear"
        differences[name] = difference
        lines.append(
            f"| {name} ({best}) | {difference:.6f} | "
            f"[{low:.6f}, {high:.6f}] | {verdict} |"
        )

    lines += [
        "",
        "## Run metadata",
        "",
        f"- Cut-off: `{iso(cutoff_time)}`",
        f"- Seed: `{seed}`",
        f"- Users: `{len(users)}`",
        f"- Database fingerprint: `{fingerprint(db_path)}`",
        f"- Git commit: `{git_commit()}`",
    ]
    (out / "baseline_table.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    chart_html = ""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(
            STRATEGIES,
            [summary[name][0] for name in STRATEGIES],
            yerr=[
                [summary[name][0] - summary[name][1] for name in STRATEGIES],
                [summary[name][2] - summary[name][0] for name in STRATEGIES],
            ],
            capsize=5,
        )
        ax.set_title("Which strategy reaches relevant posts?")
        ax.set_ylabel("Mean NDCG@10")
        fig.tight_layout()
        chart_html += f'<img alt="Strategy means" src="{png_data(fig)}">'
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 4))
        names = [name for name in GROUPS if name in differences]
        ax.bar(names, [differences[name] for name in names])
        ax.axhline(0, color="black", linewidth=1)
        ax.set_title("Does learned beat the best baseline by slice?")
        ax.set_ylabel("Learned minus baseline")
        fig.tight_layout()
        chart_html += f'<img alt="Slice differences" src="{png_data(fig)}">'
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(8, 4))
        for strategy in STRATEGIES:
            values = sorted(
                row["ndcg_at_10"] for row in rows
                if row["strategy"] == strategy
            )
            ax.plot(
                values,
                [i / len(values) for i in range(len(values))],
                label=strategy,
            )
        ax.set_title("How are user-level scores distributed?")
        ax.set_xlabel("User NDCG@10")
        ax.set_ylabel("Cumulative fraction")
        ax.legend()
        fig.tight_layout()
        chart_html += f'<img alt="Score distribution" src="{png_data(fig)}">'
        plt.close(fig)
    except ImportError:
        chart_html = "<p>Charts require the optional eval dependencies.</p>"

    (out / "dashboard.html").write_text(
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<title>InstaKill offline evaluation</title></head><body>"
        "<h1>InstaKill offline evaluation</h1>"
        + chart_html
        + "<pre>" + "\n".join(lines) + "</pre></body></html>\n",
        encoding="utf-8",
    )
    return len(users), len(rows)


def main():
    parser = argparse.ArgumentParser(description="Evaluate feed strategies")
    parser.add_argument("--db", default="instakill.db")
    parser.add_argument("--cutoff")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default="reports")
    args = parser.parse_args()
    db_path = (
        Path(args.db).resolve() if Path(args.db).is_absolute()
        else (ROOT / args.db).resolve()
    )
    out = (
        Path(args.out).resolve() if Path(args.out).is_absolute()
        else (ROOT / args.out).resolve()
    )
    cutoff_time = cutoff(db_path, args.cutoff)
    user_count, row_count = evaluate(
        db_path, cutoff_time, args.seed, out
    )
    print(f"Evaluated {user_count} users; wrote {row_count} result rows.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
