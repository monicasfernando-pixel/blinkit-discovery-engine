import streamlit as st
import requests
import json
import time
import re
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
    page_title="Spotify Discovery Analyzer",
    page_icon="🎵",
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
        background: linear-gradient(135deg, #1DB954 0%, #191414 100%);
        padding: 2rem 2.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .app-header h1 { margin: 0; font-size: 1.9rem; color: #fff; }
    .app-header p  { margin: 0.4rem 0 0; opacity: 0.85; color: #fff; font-size: 1rem; }

    .how-card {
        background: #1e1e1e;
        border: 1px solid #333;
        border-radius: 10px;
        padding: 1.2rem;
        height: 100%;
    }
    .how-card h4 { color: #1DB954; margin-top: 0; }

    .section-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1DB954;
        margin: 1.8rem 0 0.6rem;
        padding-bottom: 0.3rem;
        border-bottom: 1px solid #2a2a2a;
    }

    .quote-block {
        background: #1e1e1e;
        border-left: 3px solid #1DB954;
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
        border-left: 3px solid #1DB954;
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
    .src-reddit    { background: #ff4500; color: #fff; }
    .src-community { background: #1DB954; color: #fff; }
    .src-default   { background: #555;    color: #fff; }

    .stat-box {
        background: #1e1e1e;
        border: 1px solid #2e2e2e;
        border-radius: 8px;
        padding: 0.9rem;
        text-align: center;
    }
    .stat-box .val { font-size: 2rem; font-weight: 700; color: #1DB954; }
    .stat-box .lbl { font-size: 0.78rem; color: #888; margin-top: 0.1rem; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
SPOTIFY_APP_ID   = "324684580"
SPOTIFY_APP_SLUG = "spotify"
SPOTIFY_PLAY_ID  = "com.spotify.music"
COUNTRIES = ["us", "gb", "in", "ca", "au", "de", "fr", "br", "jp", "mx", "ng", "kr"]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
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


def fetch_appstore_reviews(n_countries: int = 8, status=None) -> List[Dict]:
    reviews: List[Dict] = []
    seen: set = set()

    for i, country in enumerate(COUNTRIES[:n_countries]):
        if status:
            status.text(f"App Store — scraping {country.upper()} ({i+1}/{n_countries})…")
        try:
            url = f"https://apps.apple.com/{country}/app/{SPOTIFY_APP_SLUG}/id{SPOTIFY_APP_ID}"
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                continue

            # Tag is: <script type="application/json" id="serialized-server-data">
            # so id= may not be the first attribute — use manual extraction
            idx = resp.text.find('serialized-server-data')
            if idx == -1:
                continue
            tag_start = resp.text.rfind('<script', 0, idx)
            open_end  = resp.text.find('>', tag_start) + 1
            close_tag = resp.text.find('</script>', open_end)
            if tag_start == -1 or close_tag == -1:
                continue

            raw = resp.text[open_end:close_tag]
            data = json.loads(raw)
            bucket: list = []
            _walk_for_reviews(data, bucket)

            for r in bucket:
                # Apple's live page uses 'contents' for review body
                text = (r.get("contents") or r.get("body") or r.get("reviewBody") or "").strip()
                if not text or len(text) < 15:
                    continue
                uid = hash(text[:80])
                if uid in seen:
                    continue
                seen.add(uid)
                reviews.append({
                    "source": "App Store",
                    "rating": r.get("rating", r.get("userRating", 0)),
                    "title":  r.get("title", ""),
                    "text":   text,
                    "date":   str(r.get("date", ""))[:10],
                    "author": r.get("reviewerName", r.get("userName", "Anonymous")),
                })

            time.sleep(0.5)
        except Exception:
            continue

    return reviews


# ── Play Store scraper ────────────────────────────────────────────────────────

def fetch_playstore_reviews(count: int = 200, status=None) -> List[Dict]:
    if status:
        status.text("Play Store — fetching reviews…")
    try:
        from google_play_scraper import reviews as gp_reviews, Sort
        result, _ = gp_reviews(
            SPOTIFY_PLAY_ID,
            lang="en", country="us",
            sort=Sort.NEWEST,
            count=count,
        )
        out = []
        for r in result:
            text = (r.get("content") or "").strip()
            if len(text) < 15:
                continue
            out.append({
                "source": "Play Store",
                "rating": r.get("score", 0),
                "title":  "",
                "text":   text,
                "date":   str(r.get("at", ""))[:10],
                "author": r.get("userName", "Anonymous"),
            })
        return out
    except Exception:
        return []


# ── Reddit scraper (no credentials — public RSS/Atom feed) ────────────────────

import xml.etree.ElementTree as ET

REDDIT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; SpotifyResearch/1.0)",
    "Accept": "application/rss+xml, application/xml, text/xml",
}
REDDIT_NS = {"atom": "http://www.w3.org/2005/Atom"}

REDDIT_QUERIES = [
    "music discovery",
    "recommendation",
    "new music",
    "discover weekly",
    "boring playlist",
    "repetitive",
]
REDDIT_SUBS = ["spotify", "musicsuggest"]


def _fetch_rss(sub: str, query: str) -> List[Dict]:
    """Fetch one Reddit RSS search feed and return parsed posts."""
    url = (
        f"https://www.reddit.com/r/{sub}/search.rss"
        f"?q={requests.utils.quote(query)}"
        f"&sort=relevance&t=year&restrict_sr=1"
    )
    try:
        resp = requests.get(url, headers=REDDIT_HEADERS, timeout=12)
        if resp.status_code != 200:
            return []
        root = ET.fromstring(resp.content)
        entries = root.findall("atom:entry", REDDIT_NS)
        posts = []
        for entry in entries:
            title   = (entry.findtext("atom:title",   "", REDDIT_NS) or "").strip()
            content = (entry.findtext("atom:content", "", REDDIT_NS) or "").strip()
            author  = (entry.findtext("atom:author/atom:name", "", REDDIT_NS) or "").strip()
            updated = (entry.findtext("atom:updated", "", REDDIT_NS) or "")[:10]
            uid     = entry.findtext("atom:id", "", REDDIT_NS) or ""

            # content is HTML — strip tags for plain text
            clean = re.sub(r"<[^>]+>", " ", content)
            clean = re.sub(r"\s+", " ", clean).strip()[:600]
            combined = f"{title}. {clean}".strip(". ")
            if len(combined) < 20:
                continue

            posts.append({
                "source": "Reddit",
                "rating": None,
                "title":  title,
                "text":   combined,
                "date":   updated,
                "author": author or "[deleted]",
                "_uid":   uid,
            })
        return posts
    except Exception:
        return []


def fetch_reddit_posts(
    client_id: str = "", client_secret: str = "",
    count: int = 100, status=None,
) -> List[Dict]:
    """Fetch Reddit posts via public RSS — no credentials required."""
    if status:
        status.text("Reddit — fetching via public RSS…")

    all_posts: List[Dict] = []
    seen: set = set()

    for sub in REDDIT_SUBS:
        for query in REDDIT_QUERIES:
            if len(all_posts) >= count:
                break
            if status:
                status.text(f"Reddit — r/{sub}: '{query}'…")

            for post in _fetch_rss(sub, query):
                uid = post.pop("_uid", post["text"][:60])
                if uid in seen:
                    continue
                seen.add(uid)
                all_posts.append(post)
                if len(all_posts) >= count:
                    break

            time.sleep(0.8)

    return all_posts[:count]


# ── Spotify Community scraper ─────────────────────────────────────────────────

def fetch_community_posts(count: int = 30, status=None) -> List[Dict]:
    if status:
        status.text("Spotify Community — fetching posts…")

    posts: List[Dict] = []
    seen: set = set()

    try:
        from bs4 import BeautifulSoup

        urls = [
            (
                "https://community.spotify.com/t5/forums/searchpage/tab/message"
                "?q=music+discovery+recommendations&include_external=no"
            ),
            "https://community.spotify.com/t5/Music/bd-p/music",
        ]

        for url in urls:
            try:
                resp = requests.get(url, headers=HEADERS, timeout=15)
                if resp.status_code != 200:
                    continue

                soup = BeautifulSoup(resp.text, "html.parser")

                for el in soup.select("a.page-link, .message-subject a, h2 a, h3 a"):
                    text = el.get_text(strip=True)
                    if len(text) < 20:
                        continue
                    uid = hash(text[:60])
                    if uid in seen:
                        continue
                    seen.add(uid)
                    posts.append({
                        "source": "Spotify Community",
                        "rating": None,
                        "title":  text,
                        "text":   text,
                        "date":   "",
                        "author": "Community User",
                    })

                time.sleep(1)
            except Exception:
                continue

    except Exception:
        pass

    return posts[:count]


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


def _analyze_batch(reviews: List[Dict], api_key: str) -> Dict:
    """Map step — extract themes/frustrations from one batch."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        system="You analyze user feedback. Respond ONLY with valid JSON, no markdown.",
        messages=[{
            "role": "user",
            "content": (
                f"Analyze these {len(reviews)} Spotify reviews focusing on music discovery.\n\n"
                f"{_fmt_batch(reviews)}\n\n"
                "Return JSON:\n"
                '{"themes":[{"theme":"...","description":"...","frequency":"high|medium|low","quote":"..."}],'
                '"frustrations":["..."],'
                '"unmet_needs":["..."],'
                '"behavioral_patterns":["..."],'
                '"segments_mentioned":["..."]}'
            ),
        }],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def _synthesize(batch_results: List[Dict], total: int, api_key: str) -> Dict:
    """Reduce step — merge all batch insights into final unified output."""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=4096,
        system="You synthesize product research. Respond ONLY with valid JSON, no markdown.",
        messages=[{
            "role": "user",
            "content": (
                f"You analyzed {total} Spotify reviews in {len(batch_results)} batches.\n"
                f"Batch insights:\n{json.dumps(batch_results, indent=2)}\n\n"
                "Synthesize into ONE unified analysis. Consolidate duplicate themes. "
                "Surface patterns that appear across multiple batches.\n\n"
                "Return EXACTLY this JSON:\n"
                '{"summary":"...","key_themes":[{"theme":"...","description":"...","frequency":"high|medium|low","quote":"..."}],'
                '"top_frustrations":["...","...","...","...","..."],'
                '"user_segments":[{"segment":"...","description":"...","pain_points":["..."]}],'
                '"unmet_needs":["...","...","...","..."],'
                '"why_discovery_fails":"...","repetitive_listening_causes":["...","...","..."],'
                '"ai_opportunities":["...","...","..."]}'
            ),
        }],
    )
    raw = msg.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


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

    return _synthesize(batch_results, len(reviews), api_key)


# ── UI helpers ────────────────────────────────────────────────────────────────

def _badge(source: str) -> str:
    cls_map = {
        "App Store":        "src-appstore",
        "Play Store":       "src-playstore",
        "Reddit":           "src-reddit",
        "Spotify Community":"src-community",
    }
    cls = cls_map.get(source, "src-default")
    return f'<span class="src-badge {cls}">{source}</span>'


def _freq_dot(freq: str) -> str:
    color = {"high": "#ff4444", "medium": "#ffaa00", "low": "#4488ff"}.get(freq, "#888")
    return f'<span style="color:{color}; font-weight:700;">{freq.upper()}</span>'


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

    # ── Summary ──
    st.markdown('<div class="section-header">Executive Summary</div>', unsafe_allow_html=True)
    st.info(insights.get("summary", ""))

    # ── Root cause ──
    st.markdown('<div class="section-header">Why Music Discovery Fails</div>', unsafe_allow_html=True)
    st.warning(insights.get("why_discovery_fails", ""))

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
        st.markdown('<div class="section-header">User Segments</div>', unsafe_allow_html=True)
        for seg in insights.get("user_segments", []):
            with st.expander(f"**{seg['segment']}**"):
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

        st.markdown(
            '<div class="section-header" style="margin-top:1.4rem">'
            'Causes of Repetitive Listening</div>',
            unsafe_allow_html=True,
        )
        for cause in insights.get("repetitive_listening_causes", []):
            st.markdown(
                f'<div class="cause-item">↺ {cause}</div>',
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
        <h1>🎵 Spotify Discovery — AI Review Analysis Engine</h1>
        <p>
            Analyze live reviews from App Store, Play Store, Reddit &amp; Spotify Community
            to understand why users struggle to discover new music.
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
    reddit_id     = _get_secret("REDDIT_CLIENT_ID")
    reddit_secret = _get_secret("REDDIT_CLIENT_SECRET")

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
        use_reddit     = st.checkbox("Reddit Discussions",   value=True)
        use_community  = st.checkbox("Spotify Community",    value=True)

        st.markdown("### Volume")
        n_countries    = st.slider("App Store — countries to scrape", 3, 12, 8,
                                   help="~24 reviews per country after dedup")
        n_playstore    = st.slider("Play Store — review count",      50, 600, 300,
                                   help="Each review goes into the analysis")
        n_reddit       = st.slider("Reddit — posts to fetch",        20, 200, 100,
                                   help="Posts from r/spotify + r/musicsuggest")

        st.markdown("---")
        run_btn = st.button("🔍 Run Analysis", type="primary", use_container_width=True)

        st.markdown("---")
        st.caption(
            "This tool fetches live public data and analyzes it with Claude. "
            "No data is stored. Built for Spotify Growth Team research."
        )

    # ── Landing state ──
    if not run_btn:
        c1, c2, c3 = st.columns(3)
        for col, (step, title, body) in zip(
            [c1, c2, c3],
            [
                ("1", "Collect",
                 "Pulls live reviews from App Store (~24/country), Google Play (200+), "
                 "Reddit discussions, and Spotify Community posts in real time."),
                ("2", "Analyze",
                 "Claude reads up to 300 reviews and extracts themes, frustrations, "
                 "user segments, unmet needs, and root-cause insights."),
                ("3", "Insight",
                 "Get a structured breakdown — ready to paste into your product deck "
                 "or export as JSON for deeper analysis."),
            ],
        ):
            with col:
                st.markdown(
                    f'<div class="how-card"><h4>Step {step} — {title}</h4><p>{body}</p></div>',
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

    # Reddit uses public JSON API — no credentials needed

    # ── Pipeline ──
    all_reviews: List[Dict] = []
    n_steps = sum([use_appstore, use_playstore, use_reddit, use_community])
    done    = 0

    progress = st.progress(0)
    status   = st.empty()

    if use_appstore:
        r = fetch_appstore_reviews(n_countries, status)
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

    if use_reddit:
        r = fetch_reddit_posts(count=n_reddit, status=status)
        all_reviews.extend(r)
        done += 1
        progress.progress(done / (n_steps + 1))
        if r:
            st.success(f"✅ Reddit — {len(r)} posts")
        else:
            st.warning("⚠️ Reddit — 0 posts (check credentials)")

    if use_community:
        r = fetch_community_posts(30, status)
        all_reviews.extend(r)
        done += 1
        progress.progress(done / (n_steps + 1))
        if r:
            st.success(f"✅ Spotify Community — {len(r)} posts")
        else:
            st.info("ℹ️ Spotify Community — 0 posts (site may be Cloudflare-protected)")

    status.empty()

    if not all_reviews:
        st.error("No reviews collected from any source. Check your configuration and try again.")
        return

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

        # Download
        st.markdown("---")
        export = {
            "generated_at":   datetime.now().isoformat(),
            "total_reviews":  len(all_reviews),
            "sources":        list({r["source"] for r in all_reviews}),
            "insights":       insights,
        }
        st.download_button(
            "⬇️ Download Full Analysis (JSON)",
            data=json.dumps(export, indent=2),
            file_name=f"spotify_discovery_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
        )

    except json.JSONDecodeError:
        st.error("Claude returned malformed JSON. Please try again.")
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        st.exception(e)


if __name__ == "__main__":
    main()
