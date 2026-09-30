"""Article fetching utility for Hacker News and RSS feeds."""

import datetime
from email.utils import parsedate_to_datetime
import json
import time
from typing import Any, Dict, List
import urllib.request
import xml.etree.ElementTree as ET

from app.firestore_sources import get_sources_for_role


def _parse_iso_date(date_str: str) -> datetime.datetime:
    """Parses ISO or common date string into timezone-aware datetime."""
    try:
        if date_str.endswith("Z"):
            date_str = date_str[:-1] + "+00:00"
        return datetime.datetime.fromisoformat(date_str)
    except Exception:
        pass
    try:
        return parsedate_to_datetime(date_str)
    except Exception:
        return datetime.datetime.now(datetime.timezone.utc)


def _fetch_hn_articles(source_name: str, category: str = "news", limit: int = 5) -> List[Dict[str, Any]]:
    """Fetches popular stories (>=100 points) from the Hacker News Algolia search API."""
    now_ts = int(time.time())
    thirty_days_ago_ts = now_ts - (30 * 24 * 3600)
    url = (
        f"https://hn.algolia.com/api/v1/search?"
        f"tags=story&numericFilters=created_at_i>{thirty_days_ago_ts},points>=100&hitsPerPage={limit}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; Loopy/1.0)"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    articles = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)
    for hit in data.get("hits", []):
        title = hit.get("title")
        if not title:
            continue
        link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        created_at_str = hit.get("created_at", "")
        dt = _parse_iso_date(created_at_str)
        if dt < cutoff:
            continue
        articles.append({
            "title": title,
            "source": source_name,
            "category": category,
            "published_date": dt.strftime("%Y-%m-%d"),
            "link": link,
        })
    return articles


def _fetch_rss_articles(source_name: str, feed_url: str, category: str = "news", limit: int = 5) -> List[Dict[str, Any]]:
    """Fetches and parses an RSS or Atom XML feed."""
    req = urllib.request.Request(feed_url, headers={"User-Agent": "Mozilla/5.0 (compatible; Loopy/1.0)"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        content = resp.read()

    root = ET.fromstring(content)
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")

    articles = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30)

    for item in items:
        title = item.findtext("title")
        if not title:
            title = item.findtext("{http://www.w3.org/2005/Atom}title")
        if not title:
            continue
        title = title.strip()

        link = item.findtext("link")
        if not link:
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
            if link_el is not None:
                link = link_el.attrib.get("href", "")
        if not link:
            continue
        link = link.strip()

        pub_date_str = (
            item.findtext("pubDate")
            or item.findtext("{http://www.w3.org/2005/Atom}published")
            or item.findtext("{http://www.w3.org/2005/Atom}updated")
            or ""
        )
        dt = _parse_iso_date(pub_date_str)
        if dt < cutoff:
            continue

        articles.append({
            "title": title,
            "source": source_name,
            "category": category,
            "published_date": dt.strftime("%Y-%m-%d"),
            "link": link,
        })
        if len(articles) >= limit:
            break

    return articles


def fetch_recent_articles_for_role(role: str) -> List[Dict[str, Any]]:
    """Fetches real recent articles from Firestore-configured sources for a role.

    Only includes articles published within the last 30 days.
    Each article includes title, source, category ('news' or 'reads'), published_date, and link.
    Gracefully skips any source that fails.
    """
    sources = get_sources_for_role(role)
    all_articles: List[Dict[str, Any]] = []

    for src in sources:
        name = src.get("name", "Unknown Source")
        url = src.get("url", "")
        src_type = src.get("type", "rss")
        category = src.get("category", "news")

        try:
            if src_type == "hackernews":
                articles = _fetch_hn_articles(source_name=name, category=category, limit=5)
            else:
                articles = _fetch_rss_articles(source_name=name, feed_url=url, category=category, limit=4)
            all_articles.extend(articles)
        except Exception:
            # Skip any feed that fails or times out
            continue

    return all_articles
