# Spotify Discovery — AI Review Analysis Engine

## What It Does

This tool analyzes **why Spotify users struggle to discover new music** by automatically collecting thousands of live public reviews from multiple platforms and running them through Claude AI to extract structured product insights.

It answers questions like:
- Why do users fail to discover new music despite Spotify's recommendation system?
- What are the most common frustrations users have with recommendations?
- Which user segments experience different discovery challenges?
- What unmet needs appear consistently across reviews?
- What causes users to fall into repetitive listening patterns?

---

## How It Works — Step by Step

### Step 1: Data Collection
When the user clicks **Run Analysis**, the app simultaneously fetches live public data from 4 sources:

| Source | Method | Volume |
|---|---|---|
| Apple App Store | Scrapes server-side rendered JSON from the App Store webpage | ~8 reviews × 8 countries = ~64 unique reviews |
| Google Play Store | `google-play-scraper` Python library | Up to 300 reviews |
| Reddit | Reddit API via PRAW — scans r/spotify and r/musicsuggest | Up to 100 posts |
| Spotify Community | HTTP scraping of public community forum pages | Up to 30 posts |

**No authentication required for App Store or Play Store.** Reddit requires a free developer app (non-commercial OAuth).

---

### Step 2: Preprocessing
Before analysis, reviews are:
1. **Filtered** — entries under 15 characters are discarded
2. **Deduplicated** — identical reviews (same text hash) are removed, especially useful for App Store where the same review appears across countries
3. **Interleaved by source** — reviews from all 4 sources are round-robin interleaved so every analysis batch contains a balanced mix of sources

---

### Step 3: AI Analysis (Map-Reduce)
All collected reviews are analyzed using a **map-reduce batching approach** — this allows the tool to analyze every single review with no hard cap:

```
All reviews (400–550 total)
    ↓ Interleaved by source
    ↓ Split into batches of 100
    ↓
[Batch 1] → Claude → {themes, frustrations, patterns}
[Batch 2] → Claude → {themes, frustrations, patterns}
[Batch 3] → Claude → {themes, frustrations, patterns}
      ...
    ↓
Final Claude call: Synthesize all batch outputs
    ↓
Unified insights JSON
```

**Why map-reduce?**
A single Claude call can only meaningfully process ~300 reviews before context quality degrades. By processing in batches of 100 and then synthesizing, the tool analyzes all 400–550 reviews without losing depth.

---

### Step 4: Insights Output
The final synthesized output includes:

- **Executive Summary** — 2–3 sentence overview of the core discovery problem
- **Key Themes** — 5–7 recurring themes with frequency rating and verbatim quotes
- **Top Frustrations** — 5 most commonly expressed frustrations
- **User Segments** — distinct user groups with different discovery challenges
- **Unmet Needs** — what users want but can't get from Spotify
- **Root Cause Analysis** — why music discovery fundamentally fails
- **Repetitive Listening Causes** — what traps users in familiar content
- **AI Opportunities** — specific AI-native solutions identified from the data
- **Download JSON** — full structured output available for export

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                        │
│                   (app.py — single file)                    │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
         ▼             ▼             ▼
  ┌────────────┐ ┌──────────┐ ┌──────────────┐
  │ App Store  │ │  Reddit  │ │  Play Store  │
  │  Scraper   │ │   PRAW   │ │   Scraper    │
  │ (requests) │ │          │ │              │
  └────────────┘ └──────────┘ └──────────────┘
         │             │             │
         └─────────────┼─────────────┘
                       │
                       ▼
            ┌────────────────────┐
            │   Preprocessing    │
            │ filter · dedup ·   │
            │ interleave sources │
            └────────────┬───────┘
                         │
                         ▼
            ┌────────────────────┐
            │   Batch Splitter   │
            │  100 reviews/batch │
            └────────────┬───────┘
                         │
               ┌─────────┼─────────┐
               ▼         ▼         ▼
          [Batch 1]  [Batch 2]  [Batch N]
               │         │         │
               └─────────┼─────────┘
                         ▼
            ┌────────────────────┐
            │   Claude Sonnet    │
            │   (Map step)       │
            │  themes per batch  │
            └────────────┬───────┘
                         │
                         ▼
            ┌────────────────────┐
            │   Claude Sonnet    │
            │  (Reduce/Synthesize│
            │    step)           │
            └────────────┬───────┘
                         │
                         ▼
            ┌────────────────────┐
            │  Insights Display  │
            │  + JSON Export     │
            └────────────────────┘
```

---

## APIs & Libraries Used

| Tool | Purpose | Cost |
|---|---|---|
| **Anthropic Claude Sonnet** | AI analysis — theme extraction, synthesis | Pay per token |
| **PRAW (Python Reddit API Wrapper)** | Reddit posts from r/spotify, r/musicsuggest | Free (non-commercial) |
| **google-play-scraper** | Google Play Store review extraction | Free |
| **requests** | HTTP client for App Store + Spotify Community scraping | Free |
| **beautifulsoup4** | HTML parsing for Spotify Community forum | Free |
| **Streamlit** | Web app framework + deployment platform | Free tier |
| **python-dotenv** | Local environment variable loading | Free |

---

## Data Sources

| Source | App ID / URL |
|---|---|
| Apple App Store | App ID `324684580` (Spotify), scraped across 12 country storefronts |
| Google Play Store | Package `com.spotify.music` |
| Reddit | Subreddits: `r/spotify`, `r/musicsuggest` |
| Spotify Community | `community.spotify.com` — Music and Ideas boards |

**Twitter/X was evaluated and excluded** — as of February 2026, X has no free API tier for new developers. All 4 included sources are freely accessible.

---

## Security & Privacy

- **No API keys are exposed in the UI** — keys are loaded silently from Streamlit Cloud secrets or a local `.env` file
- **No user data is stored** — all review data is processed in memory and discarded after the session
- **No login required** — the app fetches only publicly available reviews
- **Reddit access is read-only** — no posts, comments, or votes are made

---

## Deployment

- **Platform:** Streamlit Cloud (free tier)
- **Repo:** GitHub (public)
- **Entry point:** `app.py`
- **Secrets managed via:** Streamlit Cloud Secrets Manager
- **Runtime:** Python 3.11+

---

## Limitations

| Limitation | Detail |
|---|---|
| App Store volume | Apple SSR renders ~24 reviews per country; ~8 unique after dedup → ~64–96 total |
| Spotify Community | May be blocked by Cloudflare on some runs — results vary |
| Reddit rate limit | 100 requests/minute on free tier — adequate for this use case |
| Analysis time | ~60–90 seconds for full pipeline (4 sources + 5–6 Claude batch calls) |
| Language | English-language reviews only (by default) |
