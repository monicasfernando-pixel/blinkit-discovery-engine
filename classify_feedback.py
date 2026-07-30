import csv
import json
import os
import re
from collections import Counter
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

IN_PATH = Path("combined_feedback.csv")
OUT_PATH = Path("classified_feedback.csv")
BATCH = 25
COLS = ["source", "text", "rating_or_upvotes", "date", "labels"]
TAXONOMY = """habit_drivers — why users keep buying the same set: routines, reorder shortcuts, autopilot, list-based shopping
blockers_practical — non-trust barriers to new categories: price perception, pack sizes, delivery-fee math, "not what this app is for" mental slotting
trust_risk — quality/freshness/authenticity/expiry doubts about an unfamiliar or specific category
discovery_paths — how users find products they didn't search for: banners, browsing, word of mouth, offers, community recommendations
information_needs — what users want to know before a first-time category purchase: reviews, brand comparison, expiry visibility
trigger_events — moments that broke the routine: emergency, guests, festival, stockout, deal, life change (baby/pet/new flat), late-night need
segment_markers — signals of who experiments vs who doesn't: tenure, household type, ordering-for-others, deal-seeking, multi-app usage
unmet_needs — explicit or implied asks the platform doesn't serve: curation, bundles, "wish they had X"
noise — delivery speed, rider behaviour, refunds, app bugs, support complaints, pricing rants with NO category-behaviour signal"""
RULES = """Multi-label allowed: return a list of label names per review
noise is exclusive: if noise applies, it is the only label
If a delivery/quality complaint is tied to a category decision (e.g. "melted ice cream, never ordering frozen again"), label it trust_risk, not noise
Respond ONLY with a JSON array like [{"id": 1, "labels": ["habit_drivers"]}] — no prose, no markdown fences"""

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def extract_json(raw):
    raw = re.sub(r"^```(?:json)?\s*", "", (raw or "").strip())
    raw = re.sub(r"\s*```$", "", raw)
    start, end = raw.find("["), raw.rfind("]")
    return json.loads(raw[start:end + 1] if start != -1 and end > start else raw)


def classify_batch(texts):
    numbered = "\n".join(f"{i}. {t[:500]}" for i, t in enumerate(texts, 1))
    prompt = (
        f"Classify each Blinkit review using this taxonomy:\n\n{TAXONOMY}\n\n"
        f"Rules:\n{RULES}\n\nReviews:\n{numbered}"
    )
    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    return extract_json(msg.content[0].text)


def save_rows(rows):
    with open(OUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


with open(IN_PATH, encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))

n_batches = -(-len(rows) // BATCH)
for b in range(n_batches):
    chunk = rows[b * BATCH:(b + 1) * BATCH]
    texts = [r.get("text", "") for r in chunk]
    print(f"batch {b + 1}/{n_batches}")
    try:
        result = classify_batch(texts)
    except Exception:
        try:
            result = classify_batch(texts)
        except Exception:
            for r in chunk:
                r["labels"] = "parse_failed"
            if (b + 1) % 10 == 0 or b + 1 == n_batches:
                save_rows(rows)
            continue
    by_id = {item["id"]: item.get("labels", []) for item in result}
    for i, r in enumerate(chunk, 1):
        labels = by_id.get(i, ["parse_failed"])
        r["labels"] = ",".join(labels) if labels else "parse_failed"
    if (b + 1) % 10 == 0 or b + 1 == n_batches:
        save_rows(rows)

counts = Counter()
for r in rows:
    for lab in (r.get("labels") or "parse_failed").split(","):
        counts[lab.strip()] += 1
print("label counts:", dict(counts))
print(f"wrote {OUT_PATH} ({len(rows)} rows)")
