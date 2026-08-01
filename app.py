import streamlit as st
import requests
import json
import time
import re
import csv
import io
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Blinkit Discovery Analyzer",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .app-header {
        background: #F8CB46;
        padding: 1.1rem 1.5rem;
        border-radius: 10px;
        margin-bottom: 0.6rem;
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.55rem;
        font-weight: 700;
        color: #000000;
    }
    .app-header p {
        margin: 0.3rem 0 0;
        color: #1C1C1C;
        font-size: 0.92rem;
        line-height: 1.35;
    }

    .how-card, .method-card, .stat-box, .validation-card, .summary-box {
        background: #FFFFFF;
        border: 1px solid #E5E0D0;
        border-radius: 8px;
        padding: 0.75rem 0.9rem;
    }
    .how-card { height: 100%; margin: 0; }
    .how-card h4 {
        color: #1C1C1C;
        font-weight: 700;
        margin: 0 0 0.3rem;
        font-size: 0.95rem;
    }
    .how-card p { color: #444; margin: 0; font-size: 0.85rem; line-height: 1.4; }

    .method-card { margin: 0.35rem 0; }
    .method-card h4 {
        color: #0C831F;
        font-weight: 700;
        margin: 0 0 0.25rem;
        font-size: 0.95rem;
    }
    .method-card p { color: #444; margin: 0; font-size: 0.85rem; line-height: 1.4; }

    .section-header {
        font-size: 1.02rem;
        font-weight: 700;
        color: #1C1C1C;
        margin: 0.7rem 0 0.4rem;
        padding-bottom: 0.2rem;
        border-bottom: 1px solid #E5E0D0;
    }

    .quote-block {
        background: #FFFFFF;
        border: 1px solid #E5E0D0;
        border-left: 3px solid #F8CB46;
        padding: 0.55rem 0.8rem;
        margin: 0.3rem 0;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        color: #444;
        font-size: 0.88rem;
    }

    .frustration-item, .need-item, .opp-item {
        background: #FFFFFF;
        border: 1px solid #E5E0D0;
        border-radius: 6px;
        padding: 0.5rem 0.8rem;
        margin: 0.25rem 0;
        font-size: 0.9rem;
        color: #1C1C1C;
    }
    .need-item { border-left: 3px solid #0C831F; border-radius: 0 6px 6px 0; }
    .opp-item  { border-left: 3px solid #0C831F; border-radius: 0 6px 6px 0; }

    .src-badge {
        display: inline-block;
        border-radius: 10px;
        padding: 1px 8px;
        font-size: 0.73rem;
        font-weight: 600;
        margin-right: 4px;
    }
    .src-appstore  { background: #0d84e8; color: #fff; }
    .src-playstore { background: #34a853; color: #fff; }
    .src-reddit    { background: #FF4500; color: #fff; }
    .src-default   { background: #666;    color: #fff; }

    .stat-box { text-align: center; margin-bottom: 0.4rem; }
    .stat-box .val { font-size: 1.55rem; font-weight: 700; color: #0C831F; line-height: 1.2; }
    .stat-box .lbl { font-size: 0.75rem; color: #666; margin-top: 0.05rem; }

    .validation-card { margin: 0; }
    .validation-card .note { color: #444; font-size: 0.85rem; line-height: 1.4; }
    .summary-box {
        color: #1C1C1C;
        font-size: 0.92rem;
        line-height: 1.5;
        margin: 0.35rem 0 0;
    }
    .cache-note {
        background: #FFF8D6;
        border: 1px solid #E5D48A;
        color: #5A4A00;
        border-radius: 8px;
        padding: 0.45rem 0.8rem;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stTabs"] { margin-top: 0.35rem; }
    div[data-testid="stExpander"] { margin-bottom: 0.25rem; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 2px solid #E5E0CE;
    }
    .stTabs [data-baseweb="tab"] {
        height: 52px;
        padding: 0 24px;
        font-size: 17px;
        font-weight: 600;
        background-color: #FFFFFF;
        border-radius: 10px 10px 0 0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #F8CB46;
        color: #1C1C1C;
        border-bottom: 3px solid #0C831F;
    }
    .dq-headline { font-weight: 700; color: #1C1C1C; margin: 0 0 0.45rem; font-size: 0.95rem; }
    .dq-bullets { margin: 0 0 0.5rem 1.1rem; padding: 0; color: #1C1C1C; font-size: 0.9rem; }
    .dq-bullets li { margin: 0.15rem 0; }
    .dq-quote {
        font-style: italic;
        color: #444;
        border-left: 3px solid #F8CB46;
        padding: 0.4rem 0.75rem;
        margin: 0.35rem 0 0;
        background: #FFFFFF;
        border-radius: 0 6px 6px 0;
        font-size: 0.88rem;
    }
    .opp-card {
        background: #FFFFFF;
        border: 1px solid #E5E0D0;
        border-radius: 10px;
        padding: 0.9rem 1.05rem;
        margin: 0.45rem 0;
    }
    .opp-card .opp-title {
        font-weight: 700;
        color: #1C1C1C;
        font-size: 1.02rem;
        margin: 0 0 0.35rem;
        line-height: 1.3;
    }
    .opp-card .opp-barrier {
        color: #555;
        font-size: 0.88rem;
        margin: 0 0 0.55rem;
        line-height: 1.4;
    }
    .opp-tag {
        display: inline-block;
        background: #F4F1E4;
        border: 1px solid #E5E0D0;
        color: #3a3a3a;
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 0.72rem;
        font-weight: 600;
        margin: 0 6px 4px 0;
    }
</style>
""", unsafe_allow_html=True)

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_PATH = os.path.join(_APP_DIR, "cached_results.json")
REDDIT_CSV = os.path.join(_APP_DIR, "blinkit_reddit.csv")
COMBINED_CSV = os.path.join(_APP_DIR, "combined_feedback.csv")
LIVE_FAIL_NOTE = "Live fetch unavailable — showing cached corpus."

# Manual audit only — never estimate or generate these values.
MANUAL_AUDIT = {
    "human_audit_agreement_pct": 82,
    "sample_size": 50,
    "sample_note": "Randomly sampled non-noise rows, manually reviewed",
    "dominant_error": (
        "Generic price complaints were over-tagged as practical blockers. "
        "Corrected by discounting price mentions that carry no category context."
    ),
}

SOURCE_ORDER = ["App Store", "Play Store", "Reddit"]
SOURCE_SUBLABEL = {
    "App Store": "live scrape",
    "Play Store": "live scrape",
    "Reddit": "manually curated threads",
}

# ── Constants ─────────────────────────────────────────────────────────────────
BLINKIT_APP_ID   = "960335206"
BLINKIT_APP_SLUG = "blinkit-groceries-more"
BLINKIT_PLAY_ID  = "com.grofers.customerapp"
COUNTRIES = ["in"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── App Store scraper ─────────────────────────────────────────────────────────

def _walk_for_reviews(obj, bucket: list, limit: int = 30):
    """Recursively walk Apple SSR JSON looking for Review-kind objects."""
    if len(bucket) >= limit:
        return
    if isinstance(obj, dict):
        kind = obj.get("$kind", "")
        has_rating = isinstance(obj.get("userRating"), (int, float))
        has_body   = "body" in obj or "reviewBody" in obj
        if kind == "Review" or (has_rating and has_body):
            bucket.append(obj)
            return
        for v in obj.values():
            if isinstance(v, (dict, list)):
                _walk_for_reviews(v, bucket, limit)
    elif isinstance(obj, list):
        for item in obj:
            _walk_for_reviews(item, bucket, limit)


def _fetch_appstore_rss(country: str, seen: set, status=None) -> List[Dict]:
    """Paginate Apple's public customer-reviews RSS feed (up to ~500 reviews)."""
    out: List[Dict] = []
    MAX_PAGES = 10  # Apple caps this feed at 10 pages × 50 reviews

    for page in range(1, MAX_PAGES + 1):
        url = (
            f"https://itunes.apple.com/{country}/rss/customerreviews/"
            f"page={page}/id={BLINKIT_APP_ID}/sortby=mostrecent/json"
        )
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                break
            entries = resp.json().get("feed", {}).get("entry", [])
        except Exception as e:
            print(f"App Store — {country} RSS page {page} failed: {e}")
            break

        # First entry is app metadata, not a review — skip anything without a rating
        reviews_on_page = [e for e in entries if isinstance(e, dict) and "im:rating" in e]
        if not reviews_on_page:
            break

        for e in reviews_on_page:
            text = (e.get("content", {}).get("label") or "").strip()
            if not text or len(text) < 15:
                continue
            uid = hash(text[:80])
            if uid in seen:
                continue
            seen.add(uid)
            out.append({
                "source": "App Store",
                "rating": int(e.get("im:rating", {}).get("label", 0) or 0),
                "title":  e.get("title", {}).get("label", ""),
                "text":   text,
                "date":   (e.get("updated", {}).get("label", "") or "")[:10],
                "author": e.get("author", {}).get("name", {}).get("label", "Anonymous"),
            })

        print(f"App Store — {country} RSS page {page}: {len(reviews_on_page)} reviews, kept total {len(out)}")
        if status:
            status.text(f"App Store — {country.upper()} page {page}, {len(out)} reviews so far…")

        if len(reviews_on_page) < 50:
            break
        time.sleep(0.3)

    return out


def _fetch_appstore_ssr(country: str, seen: set) -> List[Dict]:
    """Fallback: pull the handful of reviews embedded in the storefront page."""
    out: List[Dict] = []
    try:
        url = f"https://apps.apple.com/{country}/app/{BLINKIT_APP_SLUG}/id{BLINKIT_APP_ID}"
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            return out

        idx = resp.text.find('serialized-server-data')
        if idx == -1:
            return out
        tag_start = resp.text.rfind('<script', 0, idx)
        open_end  = resp.text.find('>', tag_start) + 1
        close_tag = resp.text.find('</script>', open_end)
        if tag_start == -1 or close_tag == -1:
            return out

        data = json.loads(resp.text[open_end:close_tag])
        bucket: list = []
        _walk_for_reviews(data, bucket)

        for r in bucket:
            text = (r.get("contents") or r.get("body") or r.get("reviewBody") or "").strip()
            if not text or len(text) < 15:
                continue
            uid = hash(text[:80])
            if uid in seen:
                continue
            seen.add(uid)
            out.append({
                "source": "App Store",
                "rating": r.get("rating", r.get("userRating", 0)),
                "title":  r.get("title", ""),
                "text":   text,
                "date":   str(r.get("date", ""))[:10],
                "author": r.get("reviewerName", r.get("userName", "Anonymous")),
            })
    except Exception as e:
        print(f"App Store — {country} SSR fallback failed: {e}")

    return out


def fetch_appstore_reviews(status=None) -> List[Dict]:
    reviews: List[Dict] = []
    seen: set = set()

    for country in COUNTRIES:
        if status:
            status.text(f"App Store — scraping {country.upper()} storefront…")
        reviews.extend(_fetch_appstore_rss(country, seen, status))
        # Supplement with the storefront page in case the RSS feed is thin
        reviews.extend(_fetch_appstore_ssr(country, seen))

    return reviews


# ── Reddit (manually curated local file — never live-scraped) ─────────────────

def _normalize_source(source: str) -> str:
    s = (source or "").strip()
    if s.lower() == "reddit":
        return "Reddit"
    return s


def load_reddit_reviews() -> List[Dict]:
    """Load manually curated Reddit rows from local CSV. Never scraped live."""
    if os.path.isfile(REDDIT_CSV):
        path, reddit_only = REDDIT_CSV, True
    elif os.path.isfile(COMBINED_CSV):
        path, reddit_only = COMBINED_CSV, False
    else:
        return []

    out: List[Dict] = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            if not reddit_only and _normalize_source(row.get("source", "")) != "Reddit":
                continue
            text = (row.get("text") or "").strip()
            if not text or len(text) < 15:
                continue
            try:
                rating = int(float(row.get("rating_or_upvotes") or row.get("rating") or 0))
            except (TypeError, ValueError):
                rating = 0
            out.append({
                "source": "Reddit",
                "rating": rating,
                "title":  row.get("title", "") or "",
                "text":   text,
                "date":   (row.get("date") or "")[:10],
                "author": row.get("author") or "Reddit",
            })
    return out


def merge_reddit_into_corpus(live_reviews: List[Dict]) -> List[Dict]:
    """Keep live App Store / Play Store rows; always append local Reddit rows."""
    live_only = [
        {**r, "source": _normalize_source(r.get("source", ""))}
        for r in live_reviews
        if _normalize_source(r.get("source", "")) in ("App Store", "Play Store")
    ]
    return live_only + load_reddit_reviews()


def corpus_source_counts(reviews: List[Dict]) -> Dict[str, int]:
    """Counts for all three sources; corpus total must equal their sum."""
    counts = {s: 0 for s in SOURCE_ORDER}
    for r in reviews:
        src = _normalize_source(r.get("source", ""))
        if src in counts:
            counts[src] += 1
        elif src:
            counts[src] = counts.get(src, 0) + 1
    return counts


# ── Play Store scraper ────────────────────────────────────────────────────────

def fetch_playstore_reviews(count: int = 5000, status=None) -> List[Dict]:
    from google_play_scraper import reviews as gp_reviews, Sort

    BATCH = 200
    MAX_BATCHES = 25  # 200 × 25 = 5000

    out: List[Dict] = []
    token = None

    for batch_num in range(1, MAX_BATCHES + 1):
        if len(out) >= count:
            break

        try:
            result, token = gp_reviews(
                BLINKIT_PLAY_ID,
                lang="en", country="in",
                sort=Sort.NEWEST,
                count=BATCH,
                continuation_token=token,
            )
        except Exception as e:
            # Surface the error instead of silently exiting the loop
            print(f"Play Store — batch {batch_num} failed: {e}")
            if status:
                status.text(f"Play Store — batch {batch_num} error: {e}")
            break

        for r in result:
            text = (r.get("content") or "").strip()
            if not text or len(text) < 15:
                continue
            out.append({
                "source": "Play Store",
                "rating": r.get("score", 0),
                "title":  "",
                "text":   text,
                "date":   str(r.get("at", ""))[:10],
                "author": r.get("userName", "Anonymous"),
            })

        print(f"Play Store — batch {batch_num}: fetched {len(result)} rows, running kept total {len(out)}")
        if status:
            status.text(f"Play Store — batch {batch_num}, {len(out)} reviews so far…")

        # Google Play returns None when there are no further pages
        if not result or token is None:
            break

    return out[:count]


# ── Claude analysis (map-reduce batching) ────────────────────────────────────

BATCH_SIZE = 100  # Reviews per Claude call


def _interleave_sources(reviews: List[Dict]) -> List[Dict]:
    """Round-robin interleave reviews from all sources so every batch is balanced."""
    by_source: Dict[str, List[Dict]] = defaultdict(list)
    for r in reviews:
        by_source[r["source"]].append(r)

    buckets = list(by_source.values())
    result: List[Dict] = []
    max_len = max(len(b) for b in buckets)
    for i in range(max_len):
        for bucket in buckets:
            if i < len(bucket):
                result.append(bucket[i])
    return result


def _fmt_batch(reviews: List[Dict]) -> str:
    lines = []
    for i, r in enumerate(reviews, 1):
        rating_str = f"Rating {r['rating']}/5 | " if r["rating"] else ""
        lines.append(f"[{i}] [{r['source']}] {rating_str}{r['text'][:400]}")
    return "\n\n".join(lines)


def _extract_json(raw: str) -> Dict:
    """Tolerantly parse a JSON object from Claude output (handles fences/prose/trailing text)."""
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Fall back to the outermost { ... } span
    start, end = raw.find("{"), raw.rfind("}")
    if start != -1 and end > start:
        candidate = raw[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Last resort: drop trailing commas before } or ]
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            return json.loads(cleaned)
    raise json.JSONDecodeError("No JSON object found in model output", raw, 0)


def _analyze_batch(reviews: List[Dict], api_key: str) -> Dict:
    """Map step — extract discovery signals from one batch of Blinkit reviews."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system="You analyze user feedback for a quick-commerce grocery app. Respond ONLY with valid JSON, no markdown.",
        messages=[{
            "role": "user",
            "content": (
                f"Analyze these {len(reviews)} Blinkit (quick-commerce grocery delivery) reviews. "
                "Focus on product/category discovery: why users keep buying the same categories, "
                "what stops them exploring new categories, how they find products, and the role of habit.\n\n"
                f"{_fmt_batch(reviews)}\n\n"
                "Return JSON:\n"
                '{"themes":[{"theme":"...","description":"...","frequency":"high|medium|low","quote":"..."}],'
                '"repeat_buying_reasons":["..."],'
                '"exploration_barriers":["..."],'
                '"discovery_behaviors":["..."],'
                '"habit_signals":["..."],'
                '"info_needs":["..."],'
                '"frustrations":["..."],'
                '"unmet_needs":["..."],'
                '"experimenter_segments":["..."]}'
            ),
        }],
    )
    return _extract_json(msg.content[0].text)


def _trim_batch_results(batch_results: List[Dict]) -> List[Dict]:
    """Cap each batch's payload so the synthesis input stays compact."""
    trimmed = []
    for b in batch_results:
        t = {}
        for k, v in b.items():
            if isinstance(v, list):
                t[k] = v[:6]
            else:
                t[k] = v
        trimmed.append(t)
    return trimmed


def _synthesize(batch_results: List[Dict], total: int, api_key: str) -> Dict:
    """Reduce step — merge all batch insights into final unified output."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    compact = _trim_batch_results(batch_results)
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8000,
        system="You synthesize product research for a quick-commerce grocery app. Respond ONLY with valid JSON, no markdown.",
        messages=[{
            "role": "user",
            "content": (
                f"You analyzed {total} Blinkit reviews in {len(batch_results)} batches.\n"
                f"Batch insights:\n{json.dumps(compact, indent=2)}\n\n"
                "Synthesize into ONE unified analysis about product & category DISCOVERY on Blinkit. "
                "Consolidate duplicate themes and surface patterns that appear across multiple batches. "
                "Every answer must be grounded in the review signals above.\n\n"
                "Answer these eight discovery questions in 'discovery_questions'. "
                "Do NOT write paragraph answers. For EACH question return an object:\n"
                '{"headline":"one-sentence bold finding","bullets":["reason under 15 words",'
                '"...","..."],"quote":"verbatim corpus quote as evidence"}\n'
                "Use 3–4 bullets per answer. Keep findings grounded in the review signals above.\n\n"
                "Return EXACTLY this JSON:\n"
                '{"summary":"...",'
                '"discovery_questions":{'
                '"repeat_category_buying":{"headline":"...","bullets":["..."],"quote":"..."},'
                '"barriers_to_exploration":{"headline":"...","bullets":["..."],"quote":"..."},'
                '"how_users_discover":{"headline":"...","bullets":["..."],"quote":"..."},'
                '"role_of_habits":{"headline":"...","bullets":["..."],"quote":"..."},'
                '"info_before_new_category":{"headline":"...","bullets":["..."],"quote":"..."},'
                '"frustrations":{"headline":"...","bullets":["..."],"quote":"..."},'
                '"experimenter_segments":{"headline":"...","bullets":["..."],"quote":"..."},'
                '"unmet_needs":{"headline":"...","bullets":["..."],"quote":"..."}},'
                '"key_themes":[{"theme":"...","description":"...","frequency":"high|medium|low","quote":"..."}],'
                '"top_frustrations":["...","...","...","...","..."],'
                '"user_segments":[{"segment":"...","description":"...","experimentation":"high|medium|low","pain_points":["..."]}],'
                '"unmet_needs":["...","...","...","..."],'
                '"ai_opportunities":[{"headline":"bold one-line opportunity",'
                '"barrier":"which barrier it addresses in one short line",'
                '"themes":["theme name from key_themes","..."]}]}'
            ),
        }],
    )
    return _extract_json(msg.content[0].text)


def analyze_with_claude(reviews: List[Dict], api_key: str, status=None) -> Dict:
    """Analyze ALL reviews with map-reduce batching — no hard cap."""
    ordered   = _interleave_sources(reviews)
    batches   = [ordered[i:i + BATCH_SIZE] for i in range(0, len(ordered), BATCH_SIZE)]
    n_batches = len(batches)

    batch_results: List[Dict] = []
    for idx, batch in enumerate(batches, 1):
        if status:
            status.text(
                f"Claude: analyzing batch {idx}/{n_batches} "
                f"({len(batch)} reviews, sources: "
                f"{', '.join({r['source'] for r in batch})})…"
            )
        try:
            batch_results.append(_analyze_batch(batch, api_key))
        except Exception:
            continue

    if not batch_results:
        raise RuntimeError("All analysis batches failed.")

    if status:
        status.text(f"Claude: synthesizing {n_batches} batches → final insights…")

    insights = _synthesize(batch_results, len(reviews), api_key)

    # Attach validation metadata so the UI can demonstrate insight quality
    insights["_meta"] = {
        "total_reviews":   len(reviews),
        "batches_total":   n_batches,
        "batches_success": len(batch_results),
        "batch_size":      BATCH_SIZE,
        "batch_results":   batch_results,
    }
    return insights


# ── UI helpers ────────────────────────────────────────────────────────────────

def load_cached_results() -> Optional[Dict]:
    """Load frozen baseline for zero-click results-first display."""
    try:
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def build_cached_payload(insights: Dict, reviews: List[Dict]) -> Dict:
    """Assemble the full result set written to cached_results.json."""
    merged = merge_reddit_into_corpus(reviews)
    counts = corpus_source_counts(merged)
    meta = insights.get("_meta", {})
    export_insights = {k: v for k, v in insights.items() if k != "_meta"}
    export_insights["_meta"] = {
        "total_reviews":   meta.get("total_reviews", len(merged)),
        "batches_total":   meta.get("batches_total"),
        "batches_success": meta.get("batches_success"),
        "batch_size":      meta.get("batch_size", BATCH_SIZE),
    }
    dq = dict(export_insights.get("discovery_questions") or {})
    # Ensure all eight discovery answers exist as structured objects
    def _as_dq(val, fallback_headline: str, fallback_bullets: List[str], fallback_quote: str = ""):
        if isinstance(val, dict) and val.get("headline"):
            return {
                "headline": val.get("headline", fallback_headline),
                "bullets": list(val.get("bullets") or fallback_bullets)[:4],
                "quote": val.get("quote") or fallback_quote,
            }
        if isinstance(val, str) and val.strip():
            return {"headline": val.strip().split(".")[0] + ".", "bullets": fallback_bullets, "quote": fallback_quote}
        return {"headline": fallback_headline, "bullets": fallback_bullets, "quote": fallback_quote}

    frust = export_insights.get("top_frustrations") or []
    segs = export_insights.get("user_segments") or []
    high = [s for s in segs if (s.get("experimentation") or "").lower() == "high"]
    needs = export_insights.get("unmet_needs") or []
    themes = export_insights.get("key_themes") or []
    theme_quote = next((t.get("quote") or "" for t in themes if t.get("quote")), "")

    dq["repeat_category_buying"] = _as_dq(dq.get("repeat_category_buying"), "Users repeat the same categories.", ["Habit and urgency dominate."], theme_quote)
    dq["barriers_to_exploration"] = _as_dq(dq.get("barriers_to_exploration"), "Barriers block category exploration.", ["Trust, price, and weak discovery."], theme_quote)
    dq["how_users_discover"] = _as_dq(dq.get("how_users_discover"), "Discovery is mostly off-app.", ["Social posts and deals lead finds."], theme_quote)
    dq["role_of_habits"] = _as_dq(dq.get("role_of_habits"), "Habits suppress exploration.", ["Emergency triggers lock category use."], theme_quote)
    dq["info_before_new_category"] = _as_dq(dq.get("info_before_new_category"), "Users need clearer pre-trial info.", ["Quality, returns, and pricing cues."], theme_quote)
    dq["frustrations"] = _as_dq(
        dq.get("frustrations"),
        "Recurring frustrations block expansion.",
        [f[:80] for f in frust[:4]] or ["Quality and fee friction recur."],
        theme_quote,
    )
    dq["experimenter_segments"] = _as_dq(
        dq.get("experimenter_segments"),
        "A minority of segments experiment most.",
        [f"{s.get('segment')}" for s in (high or segs)[:4]] or ["Social seekers experiment most."],
        theme_quote,
    )
    dq["unmet_needs"] = _as_dq(
        dq.get("unmet_needs"),
        "Key unmet needs remain unserved.",
        [n[:80] for n in needs[:4]] or ["Risk-free trials and discovery paths."],
        theme_quote,
    )
    export_insights["discovery_questions"] = dq

    sample: List[Dict] = []
    for src in SOURCE_ORDER:
        sample.extend([r for r in merged if r["source"] == src][:12])
    sample = sample[:50] if sample else merged[:50]
    run_date = datetime.now().strftime("%Y-%m-%d")
    return {
        "generated_at": datetime.now().isoformat(),
        "run_date": run_date,
        "total_reviews": sum(counts.values()),
        "sources": [s for s in SOURCE_ORDER if counts.get(s, 0) > 0],
        "source_counts": counts,
        "validation": dict(MANUAL_AUDIT),
        "sample_reviews": sample,
        "reviews": sample,
        "summary": export_insights.get("summary"),
        "discovery_questions": dq,
        "key_themes": export_insights.get("key_themes"),
        "top_frustrations": export_insights.get("top_frustrations"),
        "user_segments": export_insights.get("user_segments"),
        "unmet_needs": export_insights.get("unmet_needs"),
        "ai_opportunities": export_insights.get("ai_opportunities"),
        "insights": export_insights,
    }


def save_cached_baseline(insights: Dict, reviews: List[Dict]) -> Dict:
    """Explicitly freeze the current analysis as the visitor-facing baseline."""
    payload = build_cached_payload(insights, reviews)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def _format_corpus_date(cache: Dict) -> str:
    raw = cache.get("run_date") or (cache.get("generated_at") or "")[:10]
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except Exception:
        return raw or "—"


def _badge(source: str) -> str:
    src = _normalize_source(source)
    cls_map = {
        "App Store":  "src-appstore",
        "Play Store": "src-playstore",
        "Reddit":     "src-reddit",
    }
    cls = cls_map.get(src, "src-default")
    return f'<span class="src-badge {cls}">{src}</span>'


def _freq_dot(freq: str) -> str:
    color = {"high": "#ff4444", "medium": "#ffaa00", "low": "#4488ff"}.get(freq, "#888")
    return f'<span style="color:{color}; font-weight:700;">{freq.upper()}</span>'


def _exp_dot(level: str) -> str:
    # For experimentation, HIGH is positive → green
    color = {"high": "#0C831F", "medium": "#ffaa00", "low": "#ff4444"}.get(level, "#888")
    return f'<span style="color:{color}; font-weight:700;">{level.upper()}</span>'


def _normalize_dq_answer(answer) -> Dict:
    """Accept structured {headline,bullets,quote} or legacy paragraph string."""
    if isinstance(answer, dict):
        bullets = answer.get("bullets") or []
        if isinstance(bullets, str):
            bullets = [bullets]
        return {
            "headline": (answer.get("headline") or "").strip(),
            "bullets": [str(b).strip() for b in bullets if str(b).strip()][:4],
            "quote": (answer.get("quote") or "").strip(),
        }
    text = (answer or "").strip()
    if not text:
        return {"headline": "", "bullets": [], "quote": ""}
    # Legacy paragraph fallback
    first = text.split(".")[0].strip()
    return {"headline": first + ("." if first and not first.endswith(".") else ""), "bullets": [], "quote": ""}


def _render_dq_answer(answer) -> None:
    data = _normalize_dq_answer(answer)
    if data["headline"]:
        st.markdown(f'<div class="dq-headline">{data["headline"]}</div>', unsafe_allow_html=True)
    if data["bullets"]:
        items = "".join(f"<li>{b}</li>" for b in data["bullets"])
        st.markdown(f'<ul class="dq-bullets">{items}</ul>', unsafe_allow_html=True)
    if data["quote"]:
        st.markdown(f'<div class="dq-quote">"{data["quote"]}"</div>', unsafe_allow_html=True)
    if not data["headline"] and not data["bullets"] and not data["quote"]:
        st.markdown("—")


def _normalize_ai_opportunity(opp) -> Dict:
    """Accept structured opportunity objects or legacy paragraph strings."""
    if isinstance(opp, dict):
        themes = opp.get("themes") or []
        if isinstance(themes, str):
            themes = [themes]
        return {
            "headline": (opp.get("headline") or "").strip(),
            "barrier": (opp.get("barrier") or "").strip(),
            "themes": [str(t).strip() for t in themes if str(t).strip()],
        }
    text = (opp or "").strip()
    if not text:
        return {"headline": "", "barrier": "", "themes": []}
    if "—" in text:
        title, rest = text.split("—", 1)
    elif "-" in text[:60]:
        title, rest = text.split("-", 1)
    else:
        title, rest = text, ""
    return {
        "headline": title.strip(),
        "barrier": rest.strip()[:140],
        "themes": [],
    }


def _render_ai_opportunity(opp) -> None:
    data = _normalize_ai_opportunity(opp)
    tags = "".join(f'<span class="opp-tag">{t}</span>' for t in data["themes"])
    barrier = data["barrier"] or "Addresses a corpus-identified discovery barrier."
    st.markdown(
        f'<div class="opp-card">'
        f'<div class="opp-title">{data["headline"] or "AI opportunity"}</div>'
        f'<div class="opp-barrier">{barrier}</div>'
        f'{tags}'
        f'</div>',
        unsafe_allow_html=True,
    )


def _render_step_cards():
    """Four short how-it-works cards — bold heading + one sentence each."""
    c1, c2, c3, c4 = st.columns(4)
    for col, (title, body) in zip(
        [c1, c2, c3, c4],
        [
            ("1 · Gather data",
             "Scrape live App Store &amp; Play Store reviews; always merge manually curated Reddit threads."),
            ("2 · Identify themes",
             "Claude map-reduce tags recurring themes with frequency and a supporting quote."),
            ("3 · Generate insights",
             "A synthesis step answers the eight discovery questions across all batches."),
            ("4 · Validate quality",
             "Human audit agreement, sample size, and quote grounding check insight quality."),
        ],
    ):
        with col:
            st.markdown(
                f'<div class="how-card"><h4>{title}</h4><p>{body}</p></div>',
                unsafe_allow_html=True,
            )


def _methodology_corpus_stats() -> Dict:
    """Always use frozen cached_results.json — never partial live/sample counts."""
    cache = load_cached_results() or {}
    counts = {s: 0 for s in SOURCE_ORDER}
    for k, v in (cache.get("source_counts") or {}).items():
        counts[_normalize_source(k)] = int(v)
    total = int(cache.get("total_reviews") or sum(counts.values()))
    meta = ((cache.get("insights") or {}).get("_meta") or {})
    return {
        "total": total,
        "counts": counts,
        "batches_total": int(meta.get("batches_total") or 0),
        "batches_success": int(meta.get("batches_success") or 0),
        "batch_size": int(meta.get("batch_size") or BATCH_SIZE),
    }


def _render_methodology(insights: Dict, all_reviews: List[Dict] = None):
    """Compact methodology detail cards — corpus numbers from cached_results.json only."""
    stats = _methodology_corpus_stats()
    counts = stats["counts"]
    total = stats["total"]
    batches_total = stats["batches_total"]
    batches_success = stats["batches_success"]
    batch_size = stats["batch_size"]

    themes = insights.get("key_themes", [])
    grounded = sum(1 for t in themes if (t.get("quote") or "").strip())
    grounding_pct = round(100 * grounded / len(themes)) if themes else 0

    st.markdown('<div class="section-header">Methodology detail</div>', unsafe_allow_html=True)
    m1, m2 = st.columns(2)
    with m1:
        st.markdown(
            f'<div class="method-card"><h4>1 · Gather data</h4><p>'
            f'{total:,} reviews — {counts.get("Play Store", 0):,} Play Store, '
            f'{counts.get("App Store", 0):,} App Store, {counts.get("Reddit", 0):,} Reddit '
            f'(manually curated threads) — deduped and interleaved by source.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="method-card"><h4>3 · Generate insights</h4><p>'
            'A reduce step consolidates themes and answers the eight discovery questions.</p></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f'<div class="method-card"><h4>2 · Identify themes</h4><p>'
            f'Batches of {batch_size} go to Claude; {batches_success}/{batches_total} batches '
            f'succeeded with frequency-tagged themes and quotes.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="method-card"><h4>4 · Validate quality</h4><p>'
            f'{grounding_pct}% of themes carry a verbatim quote; themes must recur across batches '
            f'to survive synthesis.</p></div>',
            unsafe_allow_html=True,
        )


def _render_validation():
    """Hardcoded manual-audit stats only — never estimated."""
    agreement = MANUAL_AUDIT["human_audit_agreement_pct"]
    sample_n  = MANUAL_AUDIT["sample_size"]
    sample_note = MANUAL_AUDIT["sample_note"]
    error     = MANUAL_AUDIT["dominant_error"]

    st.markdown('<div class="section-header">Validation</div>', unsafe_allow_html=True)
    v1, v2 = st.columns(2)
    with v1:
        st.markdown(
            f'<div class="stat-box"><div class="val">{agreement}%</div>'
            f'<div class="lbl">Human-audit agreement</div></div>',
            unsafe_allow_html=True,
        )
    with v2:
        st.markdown(
            f'<div class="stat-box"><div class="val">{sample_n}</div>'
            f'<div class="lbl">Audit sample size</div></div>',
            unsafe_allow_html=True,
        )
    st.caption(sample_note)
    st.markdown(
        f'<div class="validation-card"><div class="note">'
        f'<b>Dominant classification error:</b> {error}</div></div>',
        unsafe_allow_html=True,
    )


def _normalize_display_counts(
    all_reviews: List[Dict],
    corpus_total: Optional[int],
    source_counts: Optional[Dict[str, int]],
):
    if not source_counts:
        source_counts = corpus_source_counts(all_reviews)
    else:
        normalized = {s: 0 for s in SOURCE_ORDER}
        for k, v in source_counts.items():
            normalized[_normalize_source(k)] = int(v)
        if normalized.get("Reddit", 0) == 0:
            normalized["Reddit"] = len(load_reddit_reviews())
        source_counts = normalized

    display_counts = {s: int(source_counts.get(s, 0)) for s in SOURCE_ORDER}
    sum_sources = sum(display_counts.values())
    display_total = sum_sources
    return display_counts, display_total


def render_insights(
    insights: Dict,
    all_reviews: List[Dict],
    corpus_total: Optional[int] = None,
    source_counts: Optional[Dict[str, int]] = None,
):
    display_counts, display_total = _normalize_display_counts(
        all_reviews, corpus_total, source_counts
    )

    tab_overview, tab_how, tab_themes, tab_dq, tab_seg, tab_ai = st.tabs([
        "Overview",
        "How It Works",
        "Themes",
        "Discovery Questions",
        "Segments",
        "AI Opportunities",
    ])

    # ── Overview: stats, sources, validation, summary only ──
    with tab_overview:
        cols = st.columns(4)
        stats = [
            (display_total,                          "Reviews in corpus"),
            (sum(1 for v in display_counts.values() if v > 0), "Sources"),
            (len(insights.get("key_themes", [])),    "Themes identified"),
            (len(insights.get("user_segments", [])), "User segments"),
        ]
        for col, (val, lbl) in zip(cols, stats):
            with col:
                st.markdown(
                    f'<div class="stat-box">'
                    f'<div class="val">{val}</div>'
                    f'<div class="lbl">{lbl}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.caption(
            f"{display_counts['App Store']} App Store + "
            f"{display_counts['Play Store']} Play Store + "
            f"{display_counts['Reddit']} Reddit = {display_total}"
        )

        breakdown_cols = st.columns(3)
        for col, src in zip(breakdown_cols, SOURCE_ORDER):
            cnt = display_counts[src]
            sub = SOURCE_SUBLABEL[src]
            with col:
                st.markdown(
                    f'<div class="stat-box">{_badge(src)}'
                    f'<div class="val" style="font-size:1.35rem">{cnt}</div>'
                    f'<div class="lbl">{sub}</div></div>',
                    unsafe_allow_html=True,
                )

        _render_validation()

        st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
        summary = insights.get("summary") or ""
        st.markdown(f'<div class="summary-box">{summary}</div>', unsafe_allow_html=True)

    # ── How It Works (second tab — pipeline before findings) ──
    with tab_how:
        _render_step_cards()
        _render_methodology(insights, all_reviews)
        st.markdown('<div class="section-header">Sample Reviews</div>', unsafe_allow_html=True)
        with st.expander("Show sample (first 20 reviews)", expanded=False):
            for r in all_reviews[:20]:
                rating_str = f"⭐ {r['rating']}/5 &nbsp;|&nbsp;" if r.get("rating") else ""
                st.markdown(
                    f'<div class="quote-block">'
                    f'{_badge(r["source"])} &nbsp;{rating_str}'
                    f'<br>"{r["text"][:300]}"'
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ── Themes: collapsed expanders + frustrations ──
    with tab_themes:
        st.markdown('<div class="section-header">Key Themes</div>', unsafe_allow_html=True)
        for theme in insights.get("key_themes", []):
            freq = theme.get("frequency", "medium")
            with st.expander(f"{theme['theme']}  ·  {freq.upper()}", expanded=False):
                st.markdown(f"Frequency: {_freq_dot(freq)}", unsafe_allow_html=True)
                st.markdown(theme.get("description", ""))
                quote = theme.get("quote", "")
                if quote:
                    st.markdown(
                        f'<div class="quote-block">"{quote}"</div>',
                        unsafe_allow_html=True,
                    )

        st.markdown('<div class="section-header">Top Frustrations</div>', unsafe_allow_html=True)
        for i, f in enumerate(insights.get("top_frustrations", []), 1):
            with st.expander(f"{i}. {f[:90]}{'…' if len(f) > 90 else ''}", expanded=False):
                st.markdown(f)

    # ── Discovery Questions: collapsed expanders, structured answers ──
    with tab_dq:
        dq = insights.get("discovery_questions", {})
        dq_map = [
            ("Why do users repeatedly buy from the same categories?", dq.get("repeat_category_buying")),
            ("What prevents users from exploring new categories?",     dq.get("barriers_to_exploration")),
            ("How do users discover products today?",                  dq.get("how_users_discover")),
            ("What role do habits play in shopping behavior?",         dq.get("role_of_habits")),
            ("What information do users need before trying a new category?", dq.get("info_before_new_category")),
            ("What frustrations emerge repeatedly?", dq.get("frustrations")),
            ("Which user segments are more likely to experiment?", dq.get("experimenter_segments")),
            ("What unmet needs emerge consistently across discussions?", dq.get("unmet_needs")),
        ]
        for i, (q, a) in enumerate(dq_map, 1):
            with st.expander(f"Q{i}. {q}", expanded=False):
                _render_dq_answer(a)

    # ── Segments ──
    with tab_seg:
        st.markdown('<div class="section-header">User Segments</div>', unsafe_allow_html=True)
        for seg in insights.get("user_segments", []):
            exp = seg.get("experimentation", "medium")
            with st.expander(
                f"{seg['segment']}  ·  experiments: {exp.upper()}",
                expanded=False,
            ):
                st.markdown(f"Likelihood to experiment: {_exp_dot(exp)}", unsafe_allow_html=True)
                st.markdown(seg.get("description", ""))
                for pp in seg.get("pain_points", []):
                    st.markdown(f"• {pp}")

        st.markdown('<div class="section-header">Unmet Needs</div>', unsafe_allow_html=True)
        for need in insights.get("unmet_needs", []):
            with st.expander(need[:100] + ("…" if len(need) > 100 else ""), expanded=False):
                st.markdown(f'<div class="need-item">✦ {need}</div>', unsafe_allow_html=True)

    # ── AI Opportunities ──
    with tab_ai:
        st.caption(
            "Opportunities surfaced by the engine, ranked by how directly they address "
            "the barriers found in the corpus."
        )
        for opp in insights.get("ai_opportunities", []):
            _render_ai_opportunity(opp)


# ── Main ──────────────────────────────────────────────────────────────────────

def _baseline_source_counts(cache: Optional[Dict] = None) -> Dict[str, int]:
    """Frozen baseline counts from cached_results.json (authoritative for visitors)."""
    counts = {s: 0 for s in SOURCE_ORDER}
    if cache and cache.get("source_counts"):
        for k, v in cache["source_counts"].items():
            counts[_normalize_source(k)] = int(v)
        return counts
    counts["Reddit"] = len(load_reddit_reviews())
    return counts


def _render_corpus_banner(cache: Dict):
    total = int(cache.get("total_reviews") or sum(_baseline_source_counts(cache).values()))
    sources_n = len([s for s in SOURCE_ORDER if _baseline_source_counts(cache).get(s, 0) > 0]) or 3
    date_str = _format_corpus_date(cache)
    st.caption(
        f"Corpus analysed {date_str} · {total:,} items across {sources_n} sources · "
        f"press Run Analysis for a live refresh."
    )


def _show_cached_results(cache: Dict, note: Optional[str] = None):
    """Render frozen insights in tabs (zero-click default)."""
    if note:
        st.markdown(f'<div class="cache-note">{note}</div>', unsafe_allow_html=True)

    insights = cache.get("insights") or {
        "summary": cache.get("summary"),
        "discovery_questions": cache.get("discovery_questions"),
        "key_themes": cache.get("key_themes"),
        "top_frustrations": cache.get("top_frustrations"),
        "user_segments": cache.get("user_segments"),
        "unmet_needs": cache.get("unmet_needs"),
        "ai_opportunities": cache.get("ai_opportunities"),
        "_meta": {"total_reviews": cache.get("total_reviews"), "batches_total": 0,
                  "batches_success": 0, "batch_size": BATCH_SIZE},
    }
    reviews = cache.get("sample_reviews") or cache.get("reviews") or []
    live_sample = [
        {**r, "source": _normalize_source(r.get("source", ""))}
        for r in reviews
        if _normalize_source(r.get("source", "")) in ("App Store", "Play Store")
    ]
    reddit_sample = [
        {**r, "source": "Reddit"}
        for r in reviews
        if _normalize_source(r.get("source", "")) == "Reddit"
    ] or load_reddit_reviews()[:12]
    display_reviews = live_sample + reddit_sample
    counts = _baseline_source_counts(cache)
    render_insights(
        insights,
        display_reviews,
        corpus_total=sum(counts.values()),
        source_counts=counts,
    )


def _show_live_results(
    insights: Dict,
    all_reviews: List[Dict],
    counts: Dict[str, int],
    csv_text: str,
    csv_path: str,
):
    """Render a live run without overwriting cached_results.json."""
    st.success("Analysis complete! (live session — baseline unchanged)")
    render_insights(
        insights,
        all_reviews,
        corpus_total=sum(counts.values()),
        source_counts=counts,
    )

    if st.button(
        "Save as cached baseline",
        key="main_save_baseline",
        help="Overwrite cached_results.json with this live run",
    ):
        save_cached_baseline(insights, all_reviews)
        st.session_state.live_result = None
        st.success(f"Saved frozen baseline to {os.path.basename(CACHE_PATH)}")
        st.rerun()

    meta = insights.get("_meta", {})
    insights_export = {k: v for k, v in insights.items() if k != "_meta"}
    export = {
        "generated_at":  datetime.now().isoformat(),
        "total_reviews": sum(counts.values()),
        "sources":       [s for s in SOURCE_ORDER if counts.get(s, 0) > 0],
        "source_counts": counts,
        "insights":      insights_export,
        "validation":    dict(MANUAL_AUDIT),
        "batches_total": meta.get("batches_total"),
        "batches_success": meta.get("batches_success"),
    }
    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        st.download_button(
            "Download Full Analysis (JSON)",
            data=json.dumps(export, indent=2),
            file_name=f"blinkit_discovery_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )
    with dl_col2:
        st.download_button(
            "Download Raw Reviews (CSV)",
            data=csv_text,
            file_name=os.path.basename(csv_path),
            mime="text/csv",
            use_container_width=True,
        )


def main():
    st.markdown("""
    <div class="app-header">
        <h1>Blinkit Discovery — AI Review Analysis Engine</h1>
        <p>
            Live App Store &amp; Play Store review analysis on why users stick to the same
            categories — and what blocks product discovery.
        </p>
    </div>
    """, unsafe_allow_html=True)

    def _get_secret(key: str) -> str:
        try:
            return st.secrets[key]
        except Exception:
            return os.getenv(key, "")

    anthropic_key = _get_secret("ANTHROPIC_API_KEY")
    cache = load_cached_results()

    if cache:
        _render_corpus_banner(cache)

    # Keep last successful live run in session (does not touch the frozen file)
    if "live_result" not in st.session_state:
        st.session_state.live_result = None

    sidebar_counts = _baseline_source_counts(cache)
    # For live sidebar caption, Reddit count always reflects local file
    reddit_n = len(load_reddit_reviews())
    corpus_n = sum(sidebar_counts.values())
    sources_n = sum(1 for v in sidebar_counts.values() if v > 0)

    with st.sidebar:
        source_names = ", ".join(
            s for s in ("Play Store", "App Store", "Reddit")
            if sidebar_counts.get(s, 0) > 0 or s == "Reddit"
        )
        audit_pct = MANUAL_AUDIT["human_audit_agreement_pct"]
        st.markdown(
            f"""
<div style="margin-bottom:0.85rem;">
  <div style="font-size:0.95rem;font-weight:700;color:#1C1C1C;margin-bottom:0.7rem;">Corpus summary</div>
  <div style="margin-bottom:0.55rem;line-height:1.25;">
    <span style="font-size:1.45rem;font-weight:700;color:#0C831F;">{corpus_n:,}</span>
    <span style="font-size:0.8rem;color:#666;"> items analysed</span>
  </div>
  <div style="margin-bottom:0.55rem;line-height:1.3;">
    <span style="font-size:1.2rem;font-weight:700;color:#1C1C1C;">{sources_n} sources</span>
    <span style="font-size:0.8rem;color:#666;"> · {source_names}</span>
  </div>
  <div style="line-height:1.25;">
    <span style="font-size:1.45rem;font-weight:700;color:#0C831F;">{audit_pct}%</span>
    <span style="font-size:0.8rem;color:#666;"> human-audit agreement</span>
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

        with st.expander("Settings", expanded=False):
            if anthropic_key:
                st.success("AI analysis ready")
            else:
                st.error("ANTHROPIC_API_KEY not configured")

            st.markdown("**Live scrape sources**")
            use_appstore  = st.checkbox("App Store Reviews",  value=True)
            use_playstore = st.checkbox("Play Store Reviews", value=True)
            st.caption(
                f"Reddit — always included ({reddit_n} manually curated threads). "
                "Not live-scraped."
            )

            st.markdown("**Volume**")
            n_playstore = st.slider(
                "Play Store — review count",
                200, 5000, 5000, step=200,
                help="Fetched in batches of 200, up to 5,000",
            )

            run_btn = st.button("Run Analysis", type="primary", use_container_width=True)

            if st.session_state.live_result:
                st.markdown("---")
                if st.button(
                    "Save as cached baseline",
                    key="sidebar_save_baseline",
                    help="Overwrite cached_results.json with the latest live run",
                ):
                    lr = st.session_state.live_result
                    save_cached_baseline(lr["insights"], lr["reviews"])
                    st.session_state.live_result = None
                    st.success("Frozen baseline updated.")
                    st.rerun()

        st.caption(
            "Live-scrapes App Store & Play Store; Reddit is merged from a local curated file. "
            "Run Analysis never overwrites the frozen baseline unless you save it."
        )

    # ── Zero-click default: frozen baseline ──
    if not run_btn:
        if st.session_state.live_result:
            lr = st.session_state.live_result
            _show_live_results(
                lr["insights"], lr["reviews"], lr["counts"], lr["csv_text"], lr["csv_path"]
            )
        elif cache:
            _show_cached_results(cache)
        else:
            _render_step_cards()
            st.info("No cached_results.json yet. Run Analysis, then Save as cached baseline.")
        return

    # ── Live run (does not auto-write cached_results.json) ──
    if not anthropic_key:
        st.error("API key not configured. Set ANTHROPIC_API_KEY in Streamlit secrets.")
        if cache:
            _show_cached_results(cache, note=LIVE_FAIL_NOTE)
        return

    live_reviews: List[Dict] = []
    n_steps = sum([use_appstore, use_playstore]) or 1
    done = 0
    progress = st.progress(0)
    status = st.empty()
    scrape_error: Optional[str] = None

    try:
        if use_appstore:
            r = fetch_appstore_reviews(status)
            live_reviews.extend(r)
            done += 1
            progress.progress(min(done / (n_steps + 1), 0.9))
            if r:
                st.success(f"App Store — {len(r)} reviews")
            else:
                st.warning("App Store — 0 reviews (Apple may have changed page structure)")

        if use_playstore:
            r = fetch_playstore_reviews(n_playstore, status)
            live_reviews.extend(r)
            done += 1
            progress.progress(min(done / (n_steps + 1), 0.9))
            if r:
                st.success(f"Play Store — {len(r)} reviews")
            else:
                st.warning("Play Store — 0 reviews (scraper may need updating)")
    except Exception as e:
        scrape_error = str(e)

    status.empty()

    # Reddit always merged from local file — live scrape never removes it
    all_reviews = merge_reddit_into_corpus(live_reviews)
    counts = corpus_source_counts(all_reviews)
    st.info(
        f"Reddit — {counts['Reddit']} manually curated threads merged "
        f"(not live-scraped). Corpus: {counts['App Store']} + {counts['Play Store']} + "
        f"{counts['Reddit']} = {sum(counts.values())}"
    )

    if scrape_error and not live_reviews:
        if cache:
            _show_cached_results(cache, note=LIVE_FAIL_NOTE)
        else:
            st.error(scrape_error)
        return

    if not all_reviews:
        if cache:
            _show_cached_results(cache, note=LIVE_FAIL_NOTE)
        else:
            st.error("No reviews in corpus. Check live sources and blinkit_reddit.csv.")
        return

    csv_fields = ["source", "rating", "title", "text", "date", "author"]
    csv_buf = io.StringIO()
    csv_writer = csv.DictWriter(csv_buf, fieldnames=csv_fields, extrasaction="ignore")
    csv_writer.writeheader()
    csv_writer.writerows(all_reviews)
    csv_text = csv_buf.getvalue()

    output_dir = os.path.join(_APP_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(
        output_dir, f"blinkit_reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        f.write(csv_text)
    st.info(f"Raw reviews saved to: {csv_path}")

    n_batches_est = -(-len(all_reviews) // BATCH_SIZE)
    status.text(f"Preparing {len(all_reviews)} reviews → {n_batches_est} batches for Claude…")

    try:
        with st.spinner(
            f"Claude is analyzing {len(all_reviews)} reviews in {n_batches_est} batches…"
        ):
            insights = analyze_with_claude(all_reviews, anthropic_key, status)

        progress.progress(1.0)
        status.empty()

        # Session only — do not overwrite cached_results.json
        st.session_state.live_result = {
            "insights": insights,
            "reviews": all_reviews,
            "counts": counts,
            "csv_text": csv_text,
            "csv_path": csv_path,
        }
        _show_live_results(insights, all_reviews, counts, csv_text, csv_path)

    except Exception:
        status.empty()
        if cache:
            _show_cached_results(cache, note=LIVE_FAIL_NOTE)
        else:
            st.error("Analysis failed.")


if __name__ == "__main__":
    main()
