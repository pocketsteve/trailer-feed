#!/usr/bin/env python3
"""
YouTube Trailer RSS Feed Generator
-----------------------------------
Fetches Atom feeds for a list of YouTube channels, filters entries whose
titles contain any of the configured keywords, and writes a combined RSS
2.0 feed to docs/feed.xml (served via GitHub Pages).
"""

import os
import sys
import yaml
import feedparser
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.etree.ElementTree import Element, SubElement, tostring
import xml.etree.ElementTree as ET

CONFIG_FILE  = "channels.yaml"
OUTPUT_FILE  = os.path.join("docs", "feed.xml")

# This is my test feed
# OUTPUT_FILE  = os.path.join("docs", "feed_trial.xml") 


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_channel_feed(channel_id: str):
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    return feedparser.parse(url)


def matches_filter(title: str, keywords: list[str]) -> bool:
    lower = title.lower()
    return any(kw.lower() in lower for kw in keywords)


def entry_datetime(entry) -> datetime:
    if getattr(entry, "published_parsed", None):
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    return datetime.min.replace(tzinfo=timezone.utc)


def get_thumbnail(entry) -> str:
    thumbnails = getattr(entry, "media_thumbnail", [])
    if thumbnails:
        return thumbnails[0].get("url", "")
    return ""


def get_description(entry) -> str:
    """Return a plain-text summary with a thumbnail image tag prepended."""
    summary = getattr(entry, "summary", "") or ""
    thumb   = get_thumbnail(entry)
    if thumb:
        img = f'<img src="{thumb}" alt="thumbnail" style="max-width:100%"/><br/>'
        summary = summary.replace('\n', '<br />')
        return img + summary
    return summary


# ---------------------------------------------------------------------------
# RSS builder
# ---------------------------------------------------------------------------

def build_rss(entries: list[dict], config: dict) -> str:
    rss = Element("rss", version="2.0")
    rss.set("xmlns:media",   "http://search.yahoo.com/mrss/")
    rss.set("xmlns:content", "http://purl.org/rss/1.0/modules/content/")
    rss.set("xmlns:atom",    "http://www.w3.org/2005/Atom")

    ch = SubElement(rss, "channel")
    SubElement(ch, "title").text       = config.get("feed_title",       "Film Trailers")
    SubElement(ch, "link").text        = config.get("feed_link",        "https://www.youtube.com")
    SubElement(ch, "description").text = config.get("feed_description", "Latest film trailers from major studios")
    SubElement(ch, "language").text    = "en-us"
    SubElement(ch, "lastBuildDate").text = format_datetime(datetime.now(timezone.utc))

    for e in entries:
        item = SubElement(ch, "item")
        SubElement(item, "title").text   = f"[{e['channel_name']}] {e['title']}"
        SubElement(item, "link").text    = e["link"]
        SubElement(item, "guid", isPermaLink="true").text = e["link"]
        SubElement(item, "pubDate").text = format_datetime(e["published"])

        desc = SubElement(item, "description")
        desc.text = e.get("description", "")

        if e.get("thumbnail"):
            mt = SubElement(item, "media:thumbnail")
            mt.set("url", e["thumbnail"])

    # Pretty-print
    ET.indent(rss, space="  ")          # requires Python ≥ 3.9
    raw = tostring(rss, encoding="unicode", xml_declaration=False)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + raw + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not os.path.exists(CONFIG_FILE):
        sys.exit(f"Config file not found: {CONFIG_FILE}")

    config   = load_config(CONFIG_FILE)
    channels = config.get("channels", [])
    keywords = config.get("filter_keywords", ["trailer", "teaser"])

    print(f"Channels : {len(channels)}")
    print(f"Keywords : {keywords}\n")

    all_entries: list[dict] = []
    errors: list[str] = []

    for ch in channels:
        name       = ch.get("name", "Unknown")
        channel_id = ch.get("id", "").strip()

        if not channel_id:
            errors.append(f"SKIP  {name}: missing channel ID")
            continue

        try:
            feed = fetch_channel_feed(channel_id)
        except Exception as exc:
            errors.append(f"ERROR {name}: {exc}")
            continue

        matched = 0
        for entry in feed.entries:
            if matches_filter(entry.title, keywords):
                all_entries.append({
                    "title":        entry.title,
                    "link":         entry.link,
                    "published":    entry_datetime(entry),
                    "channel_name": name,
                    "description":  get_description(entry),
                    "thumbnail":    get_thumbnail(entry),
                })
                matched += 1

        total = len(feed.entries)
        status = "⚠ feed empty" if total == 0 else f"{matched}/{total} matched"
        print(f"  {name:<30} {status}")

    if errors:
        print()
        for e in errors:
            print(f"  {e}", file=sys.stderr)

    # Newest first
    all_entries.sort(key=lambda x: x["published"], reverse=True)
    print(f"\nTotal trailers: {len(all_entries)}")

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    rss_xml = build_rss(all_entries, config)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print(f"Feed written → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
