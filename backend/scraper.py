"""Firecrawl scraping and Pandas cleanup."""
import json, os, datetime as dt
from pathlib import Path
import pandas as pd
import requests

SOURCES = json.loads((Path(__file__).parent / "sources.json").read_text())
MAX_CHARS = 3000  # keep the LLM prompt small and cheap


def load_sources():
    return SOURCES


def scrape_one(src):
    key = os.getenv("FIRECRAWL_API_KEY")
    r = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {key}"},
        json={"url": src["url"], "formats": ["markdown"], "onlyMainContent": True},
        timeout=60,
    )
    r.raise_for_status()
    md = r.json().get("data", {}).get("markdown", "")
    return {
        "source": src["name"],
        "url": src["url"],
        "category": src["category"],
        "content": md,
        "date": dt.date.today().isoformat(),
    }


def scrape_sources():
    """Returns a cleaned DataFrame (empty if no Firecrawl key -> demo mode)."""
    if not os.getenv("FIRECRAWL_API_KEY"):
        return pd.DataFrame()
    rows = []
    for src in SOURCES:
        try:
            rows.append(scrape_one(src))
        except Exception as e:  # one failed site should not kill the briefing
            print(f"[scrape failed] {src['name']}: {e}")
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["content"] = df["content"].str.strip().str.slice(0, MAX_CHARS)
    df = df[df["content"].str.len() > 200].drop_duplicates(subset="content")
    return df