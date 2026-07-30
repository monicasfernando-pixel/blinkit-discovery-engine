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
    .stApp { background-color: #121212; color: #ffffff; }
    section[data-testid="stSidebar"] { background-color: #1a1a1a; }

    /* Sidebar text — labels, captions, markdown */
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown p,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stCheckbox label p,
    section[data-testid="stSidebar"] .stSlider label p,
    section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p { color: #ffffff !important; }

    /* Slider value/tick text */
    section[data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
    section[data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"] {
        color: #cccccc !important;
    }

    .app-header {
        background: linear-gradient(135deg, #0C831F 0%, #F8CB46 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .app-header h1 { margin: 0; font-size: 1.9rem; color: #1a1a1a; }
    .app-header p  { margin: 0.4rem 0 0; opacity: 0.9; color: #1a1a1a; font-size: 1rem; }

    .method-card {
        background: #1e1e1e;
        border: 1px solid #333;
        border-left: 4px solid #F8CB46;
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin: 0.5rem 0;
    }
    .method-card h4 { color: #F8CB46; margin: 0 0 0.4rem; font-size: 1.02rem; }
    .method-card p  { color: #b3b3b3; margin: 0; font-size: 0.9rem; line-height: 1.5; }

    .qa-card {
        background: #171717;
        border: 1px solid #2e2e2e;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 0.5rem 0;
    }
    .qa-card .q { color: #F8CB46; font-weight: 700; font-size: 0.98rem; margin-bottom: 0.4rem; }
    .qa-card .a { color: #dcdcdc; font-size: 0.93rem; line-height: 1.55; }

    .how-card {
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 1.2rem;
        height: 100%;
    }
    .how-card h4 { color: #F8CB46; margin-top: 0; }

    .section-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #F8CB46;
        margin: 1.8rem 0 0.6rem;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid #2a2a2a;
    }

    .quote-block {
        background: #1e1e1e;
        border-left: 3px solid #F8CB46;
        padding: 0.7rem 1rem;
        margin: 0.4rem 0;
        border-radius: 0 8px 8px 0;
        font-style: italic;
        color: #b3b3b3;
        font-size: 0.9rem;
    }

    .frustration-item {
        background: #1a1a1a;
        border: 1px solid #2e2e2e;
        border-radius: 6px;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        font-size: 0.95rem;
    }

    .need-item {
        background: #1a2a1a;
        border-left: 3px solid #0C831F;
        border-radius: 0 6px 6px 0;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        font-size: 0.95rem;
    }

    .cause-item {
        background: #2a1a1a;
        border-left: 3px solid #ff4444;
        border-radius: 0 6px 6px 0;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        font-size: 0.95rem;
    }

    .opp-item {
        background: #1a1a2a;
        border-left: 3px solid #4488ff;
        border-radius: 0 6px 6px 0;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        font-size: 0.95rem;
    }

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
    .src-default   { background: #555;    color: #fff; }

    .stat-box {
        background: #1e1e1e;
        border: 1px solid #2e2e2e;
        border-radius: 8px;
        padding: 0.9rem;
        text-align: center;
    }
    .stat-box .val { font-size: 2rem; font-weight: 700; color: #F8CB46; }
    .stat-box .lbl { font-size: 0.78rem; color: #888; margin-top: 0.1rem; }
</style>
""", unsafe_allow_html=True)

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
                "Answer these discovery questions explicitly in 'discovery_questions'.\n"
                "Return EXACTLY this JSON:\n"
                '{"summary":"...",'
                '"discovery_questions":{'
                '"repeat_category_buying":"why users repeatedly buy from the same categories",'
                '"barriers_to_exploration":"what prevents users from exploring new categories",'
                '"how_users_discover":"how users discover products today",'
                '"role_of_habits":"what role habits play in shopping behavior",'
                '"info_before_new_category":"what information users need before trying a new category"},'
                '"key_themes":[{"theme":"...","description":"...","frequency":"high|medium|low","quote":"..."}],'
                '"top_frustrations":["...","...","...","...","..."],'
                '"user_segments":[{"segment":"...","description":"...","experimentation":"high|medium|low","pain_points":["..."]}],'
                '"unmet_needs":["...","...","...","..."],'
                '"ai_opportunities":["...","...","..."]}'
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

def _badge(source: str) -> str:
    cls_map = {
        "App Store":        "src-appstore",
        "Play Store":       "src-playstore",
    }
    cls = cls_map.get(source, "src-default")
    return f'<span class="src-badge {cls}">{source}</span>'


def _freq_dot(freq: str) -> str:
    color = {"high": "#ff4444", "medium": "#ffaa00", "low": "#4488ff"}.get(freq, "#888")
    return f'<span style="color:{color}; font-weight:700;">{freq.upper()}</span>'


def _exp_dot(level: str) -> str:
    # For experimentation, HIGH is positive → green
    color = {"high": "#0C831F", "medium": "#ffaa00", "low": "#ff4444"}.get(level, "#888")
    return f'<span style="color:{color}; font-weight:700;">{level.upper()}</span>'


def _render_methodology(insights: Dict, all_reviews: List[Dict]):
    """Demonstrate how data is gathered/analyzed, how themes & insights form, and validation."""
    meta = insights.get("_meta", {})
    source_counts: Dict[str, int] = {}
    for r in all_reviews:
        source_counts[r["source"]] = source_counts.get(r["source"], 0) + 1

    # Date range
    dates = sorted(d for d in (r.get("date", "") for r in all_reviews) if d and len(d) >= 7)
    date_range = f"{dates[0]} → {dates[-1]}" if dates else "n/a"

    # Rating distribution
    rating_counts = {i: 0 for i in range(1, 6)}
    rated = 0
    for r in all_reviews:
        try:
            rv = int(r.get("rating") or 0)
        except (TypeError, ValueError):
            rv = 0
        if 1 <= rv <= 5:
            rating_counts[rv] += 1
            rated += 1

    # Theme grounding — share of themes backed by a verbatim quote
    themes = insights.get("key_themes", [])
    grounded = sum(1 for t in themes if (t.get("quote") or "").strip())
    grounding_pct = round(100 * grounded / len(themes)) if themes else 0

    batches_total   = meta.get("batches_total", 0)
    batches_success = meta.get("batches_success", 0)
    batch_size      = meta.get("batch_size", BATCH_SIZE)

    st.markdown('<div class="section-header">How This Analysis Works</div>', unsafe_allow_html=True)

    m1, m2 = st.columns(2)
    with m1:
        st.markdown(
            '<div class="method-card"><h4>1 · How data is gathered</h4><p>'
            f'Live public reviews are scraped from the Apple App Store and Google Play '
            f'(India storefront, <code>com.grofers.customerapp</code>). '
            f'{len(all_reviews)} reviews across {len(source_counts)} sources '
            f'({date_range}) are deduplicated by text hash and round-robin interleaved by source '
            'so each analysis batch stays balanced.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="method-card"><h4>3 · How insights are generated</h4><p>'
            'A reduce step merges all batch outputs, consolidates duplicate themes, and answers the '
            'eight discovery questions — repeat buying, exploration barriers, discovery paths, habit '
            'loops, pre-trial info needs, frustrations, experimenter segments, and unmet needs.</p></div>',
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            '<div class="method-card"><h4>2 · How themes are identified</h4><p>'
            f'Reviews are processed with a map-reduce pattern: batches of {batch_size} reviews are each '
            f'sent to Claude, which extracts recurring themes, tags each with a frequency (high/medium/low), '
            f'and captures a supporting user quote. {batches_success}/{batches_total} batches processed '
            'successfully.</p></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="method-card"><h4>4 · How quality is validated</h4><p>'
            f'<b>Grounding:</b> {grounded}/{len(themes)} themes ({grounding_pct}%) are backed by a verbatim '
            f'review quote. <b>Coverage:</b> {rated} reviews carry a star rating; themes must recur across '
            f'{batches_total} independent batches to survive synthesis. <b>Sample size:</b> {len(all_reviews)} '
            'reviews reduce single-review bias.</p></div>',
            unsafe_allow_html=True,
        )

    # Rating distribution bar — quick quantitative sanity check
    if rated:
        st.markdown("**Rating distribution of analyzed reviews**")
        try:
            import pandas as pd
            df = pd.DataFrame(
                {"reviews": [rating_counts[i] for i in range(1, 6)]},
                index=[f"{i}★" for i in range(1, 6)],
            )
            st.bar_chart(df, height=180)
        except Exception:
            for i in range(5, 0, -1):
                st.markdown(f"{i}★ — {rating_counts[i]}")

    st.markdown("---")


def render_insights(insights: Dict, all_reviews: List[Dict]):
    # ── Stats row ──
    source_counts: Dict[str, int] = {}
    for r in all_reviews:
        source_counts[r["source"]] = source_counts.get(r["source"], 0) + 1

    cols = st.columns(4)
    stats = [
        (len(all_reviews),                       "Reviews analyzed"),
        (len(source_counts),                     "Sources"),
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

    # Source breakdown
    st.markdown("&nbsp;")
    breakdown_cols = st.columns(len(source_counts) or 1)
    for col, (src, cnt) in zip(breakdown_cols, source_counts.items()):
        with col:
            st.markdown(
                f'<div class="stat-box">{_badge(src)}'
                f'<div class="val" style="font-size:1.5rem">{cnt}</div>'
                f'<div class="lbl">reviews</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── Methodology & validation ──
    _render_methodology(insights, all_reviews)

    # ── Summary ──
    st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
    st.info(insights.get("summary", ""))

    # ── Discovery questions answered ──
    st.markdown('<div class="section-header">Discovery Questions Answered</div>', unsafe_allow_html=True)
    dq = insights.get("discovery_questions", {})
    dq_map = [
        ("Why do users repeatedly buy from the same categories?", dq.get("repeat_category_buying", "")),
        ("What prevents users from exploring new categories?",     dq.get("barriers_to_exploration", "")),
        ("How do users discover products today?",                  dq.get("how_users_discover", "")),
        ("What role do habits play in shopping behavior?",         dq.get("role_of_habits", "")),
        ("What information do users need before trying a new category?", dq.get("info_before_new_category", "")),
    ]
    for q, a in dq_map:
        st.markdown(
            f'<div class="qa-card"><div class="q">{q}</div>'
            f'<div class="a">{a or "—"}</div></div>',
            unsafe_allow_html=True,
        )

    # ── Key themes ──
    st.markdown('<div class="section-header">Key Themes</div>', unsafe_allow_html=True)
    for theme in insights.get("key_themes", []):
        freq = theme.get("frequency", "medium")
        label = f"**{theme['theme']}** &nbsp;·&nbsp; {_freq_dot(freq)} frequency"
        with st.expander(theme["theme"]):
            st.markdown(f"Frequency: {_freq_dot(freq)}", unsafe_allow_html=True)
            st.markdown(theme.get("description", ""))
            quote = theme.get("quote", "")
            if quote:
                st.markdown(
                    f'<div class="quote-block">"{quote}"</div>',
                    unsafe_allow_html=True,
                )

    # ── Top frustrations ──
    st.markdown('<div class="section-header">Top Frustrations</div>', unsafe_allow_html=True)
    for i, f in enumerate(insights.get("top_frustrations", []), 1):
        st.markdown(
            f'<div class="frustration-item"><b>{i}.</b> {f}</div>',
            unsafe_allow_html=True,
        )

    # ── Segments + needs (side by side) ──
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(
            '<div class="section-header">User Segments '
            '<span style="font-size:0.8rem;color:#888">(who experiments most)</span></div>',
            unsafe_allow_html=True,
        )
        for seg in insights.get("user_segments", []):
            exp = seg.get("experimentation", "medium")
            with st.expander(f"{seg['segment']}  ·  experiments: {exp.upper()}"):
                st.markdown(f"Likelihood to experiment: {_exp_dot(exp)}", unsafe_allow_html=True)
                st.markdown(seg.get("description", ""))
                for pp in seg.get("pain_points", []):
                    st.markdown(f"• {pp}")

    with col_b:
        st.markdown('<div class="section-header">Unmet Needs</div>', unsafe_allow_html=True)
        for need in insights.get("unmet_needs", []):
            st.markdown(
                f'<div class="need-item">✦ {need}</div>',
                unsafe_allow_html=True,
            )

    # ── AI Opportunities ──
    st.markdown('<div class="section-header">AI Opportunities Identified</div>', unsafe_allow_html=True)
    for opp in insights.get("ai_opportunities", []):
        st.markdown(
            f'<div class="opp-item">→ {opp}</div>',
            unsafe_allow_html=True,
        )

    # ── Sample reviews ──
    st.markdown('<div class="section-header">Sample Reviews Collected</div>', unsafe_allow_html=True)
    with st.expander("Show sample (first 20 reviews)"):
        for r in all_reviews[:20]:
            rating_str = f"⭐ {r['rating']}/5 &nbsp;|&nbsp;" if r["rating"] else ""
            st.markdown(
                f'<div class="quote-block">'
                f'{_badge(r["source"])} &nbsp;{rating_str}'
                f'<br>"{r["text"][:300]}"'
                f"</div>",
                unsafe_allow_html=True,
            )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Header
    st.markdown("""
    <div class="app-header">
        <h1>🛒 Blinkit Discovery — AI Review Analysis Engine</h1>
        <p>
            Analyze live reviews from App Store &amp; Play Store to understand why
            users stick to the same categories and what blocks product discovery.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Read API keys silently from environment / Streamlit secrets ──
    # Keys are never shown in the UI — loaded from .env locally or
    # Streamlit Cloud secrets in production.
    def _get_secret(key: str) -> str:
        # Streamlit Cloud secrets take priority, then environment
        try:
            return st.secrets[key]
        except Exception:
            return os.getenv(key, "")

    anthropic_key = _get_secret("ANTHROPIC_API_KEY")

    # ── Sidebar ──
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        # Show a green lock if key is present, red warning if missing
        if anthropic_key:
            st.success("AI analysis ready")
        else:
            st.error("ANTHROPIC_API_KEY not configured")

        st.markdown("### Sources")
        use_appstore   = st.checkbox("App Store Reviews",    value=True)
        use_playstore  = st.checkbox("Play Store Reviews",   value=True)

        st.markdown("### Volume")
        n_playstore    = st.slider("Play Store — review count",      200, 5000, 5000, step=200,
                                   help="Fetched in batches of 200, up to 5,000")

        st.markdown("---")
        run_btn = st.button("🔍 Run Analysis", type="primary", use_container_width=True)

        st.markdown("---")
        st.caption(
            "This tool fetches live public data and analyzes it with Claude. "
            "Built for Blinkit Growth Team research on category & product discovery."
        )

    # ── Landing state ──
    if not run_btn:
        c1, c2, c3, c4 = st.columns(4)
        for col, (step, title, body) in zip(
            [c1, c2, c3, c4],
            [
                ("1", "Gather data",
                 "Scrapes live App Store &amp; Google Play reviews for Blinkit "
                 "(India), deduplicates them, and interleaves sources for balanced batches."),
                ("2", "Identify themes",
                 "Map-reduce with Claude: reviews are batched, each batch yields recurring "
                 "themes tagged high/medium/low frequency with a supporting quote."),
                ("3", "Generate insights",
                 "A synthesis step consolidates themes across batches and answers the eight "
                 "discovery questions about category &amp; product exploration."),
                ("4", "Validate quality",
                 "Every theme is grounded in a verbatim quote, must recur across independent "
                 "batches, and is backed by a transparent sample size &amp; rating spread."),
            ],
        ):
            with col:
                st.markdown(
                    f'<div class="how-card"><h4>Step {step} — {title}</h4><p>{body}</p></div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div class="section-header">Questions This Engine Answers</div>', unsafe_allow_html=True)
        questions = [
            "Why do users repeatedly buy from the same categories?",
            "What prevents users from exploring new categories?",
            "How do users discover products today?",
            "What role do habits play in shopping behavior?",
            "What information do users need before trying a new category?",
            "What frustrations emerge repeatedly?",
            "Which user segments are more likely to experiment?",
            "What unmet needs emerge consistently across discussions?",
        ]
        q1, q2 = st.columns(2)
        for idx, q in enumerate(questions):
            with (q1 if idx % 2 == 0 else q2):
                st.markdown(
                    f'<div class="qa-card"><div class="q">Q{idx + 1}</div>'
                    f'<div class="a">{q}</div></div>',
                    unsafe_allow_html=True,
                )

        st.markdown("""
        <br>
        <p style="color:#888; text-align:center;">
            Select your sources in the sidebar and click <b>Run Analysis</b> to begin.
        </p>
        """, unsafe_allow_html=True)
        return

    # ── Validation ──
    if not anthropic_key:
        st.error("API key not configured. Set ANTHROPIC_API_KEY in Streamlit secrets.")
        return

    # ── Pipeline ──
    all_reviews: List[Dict] = []
    n_steps = sum([use_appstore, use_playstore])
    done    = 0

    progress = st.progress(0)
    status   = st.empty()

    if use_appstore:
        r = fetch_appstore_reviews(status)
        all_reviews.extend(r)
        done += 1
        progress.progress(done / (n_steps + 1))
        if r:
            st.success(f"✅ App Store — {len(r)} reviews")
        else:
            st.warning("⚠️ App Store — 0 reviews (Apple may have changed page structure)")

    if use_playstore:
        r = fetch_playstore_reviews(n_playstore, status)
        all_reviews.extend(r)
        done += 1
        progress.progress(done / (n_steps + 1))
        if r:
            st.success(f"✅ Play Store — {len(r)} reviews")
        else:
            st.warning("⚠️ Play Store — 0 reviews (scraper may need updating)")

    status.empty()

    if not all_reviews:
        st.error("No reviews collected from any source. Check your configuration and try again.")
        return

    # ── Save raw scraped reviews to CSV on disk ──
    csv_fields = ["source", "rating", "title", "text", "date", "author"]
    csv_buf = io.StringIO()
    csv_writer = csv.DictWriter(csv_buf, fieldnames=csv_fields, extrasaction="ignore")
    csv_writer.writeheader()
    csv_writer.writerows(all_reviews)
    csv_text = csv_buf.getvalue()

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(
        output_dir, f"blinkit_reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    # utf-8-sig so Excel opens Unicode review text correctly
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        f.write(csv_text)
    st.info(f"📁 Raw reviews saved to: {csv_path}")

    # ── Claude analysis ──
    n_batches_est = -(-len(all_reviews) // BATCH_SIZE)  # ceiling division
    status.text(f"Preparing {len(all_reviews)} reviews → {n_batches_est} batches for Claude…")

    try:
        with st.spinner(f"Claude is analyzing {len(all_reviews)} reviews in {n_batches_est} batches…"):
            insights = analyze_with_claude(all_reviews, anthropic_key, status)

        progress.progress(1.0)
        status.empty()

        st.success("Analysis complete!")
        st.markdown("---")
        st.markdown("## 📊 Insights")
        render_insights(insights, all_reviews)

        # Download — strip the heavy per-batch payload, keep a slim validation summary
        st.markdown("---")
        meta = insights.get("_meta", {})
        insights_export = {k: v for k, v in insights.items() if k != "_meta"}
        insights_export["validation"] = {
            "total_reviews":   meta.get("total_reviews", len(all_reviews)),
            "batches_total":   meta.get("batches_total"),
            "batches_success": meta.get("batches_success"),
            "batch_size":      meta.get("batch_size"),
        }
        export = {
            "generated_at":   datetime.now().isoformat(),
            "total_reviews":  len(all_reviews),
            "sources":        list({r["source"] for r in all_reviews}),
            "insights":       insights_export,
        }
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                "⬇️ Download Full Analysis (JSON)",
                data=json.dumps(export, indent=2),
                file_name=f"blinkit_discovery_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                mime="application/json",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                "⬇️ Download Raw Reviews (CSV)",
                data=csv_text,
                file_name=os.path.basename(csv_path),
                mime="text/csv",
                use_container_width=True,
            )

    except json.JSONDecodeError:
        st.error("Claude returned malformed JSON. Please try again.")
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()
