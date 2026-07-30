import csv
import json
from datetime import datetime, timezone
from pathlib import Path

FOLDER = Path("reddit_threads")
OUT = Path("blinkit_reddit.csv")
COLS = ["source", "text", "rating_or_upvotes", "date"]


def to_date(utc):
    return datetime.fromtimestamp(float(utc), tz=timezone.utc).strftime("%Y-%m-%d")


def keep_comment(body, author):
    body = (body or "").strip()
    if body in ("[deleted]", "[removed]") or author == "AutoModerator":
        return False
    return len(body) >= 15


def walk_comments(children, rows):
    for child in children or []:
        if child.get("kind") != "t1":
            continue
        d = child["data"]
        body, author = d.get("body", ""), d.get("author", "")
        if keep_comment(body, author):
            rows.append(["reddit", body.strip(), d.get("score", 0), to_date(d["created_utc"])])
        replies = d.get("replies")
        if isinstance(replies, dict):
            walk_comments(replies.get("data", {}).get("children", []), rows)


rows, seen, n_files = [], set(), 0
for path in sorted(FOLDER.glob("*.json")):
    n_files += 1
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    post = data[0]["data"]["children"][0]["data"]
    pid = post["id"]
    if pid in seen:
        continue
    seen.add(pid)
    text = f"{post.get('title', '').strip()} {post.get('selftext', '').strip()}".strip()
    if len(text) >= 15:
        rows.append(["reddit", text, post.get("score", 0), to_date(post["created_utc"])])
    walk_comments(data[1]["data"]["children"], rows)

with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(COLS)
    w.writerows(rows)

print(f"files read: {n_files}")
print(f"rows written: {len(rows)}")
