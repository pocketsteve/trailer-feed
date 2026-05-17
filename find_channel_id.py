#!/usr/bin/env python3
"""
find_channel_id.py
------------------
Looks up the internal channel ID (UCxxxxxxxxxxxxxxxxxxxxxxxxx) for a YouTube
channel given its handle or URL, then prints the RSS feed URL ready to paste
into channels.yaml.

Usage:
    python find_channel_id.py @A24
    python find_channel_id.py @WarnerBros
    python find_channel_id.py https://www.youtube.com/@Netflix

Requires no third-party libraries.
"""

import sys
import re
import urllib.request
import urllib.error

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

# Channel ID pattern: always starts with UC, 24 chars total
CHANNEL_ID_RE = re.compile(r'"(UC[a-zA-Z0-9_-]{22})"')

# Patterns to look for in the page source
SEARCH_PATTERNS = [
    re.compile(r'"channelId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"'),
    re.compile(r'"externalId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"'),
    re.compile(r'"browseId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"'),
    re.compile(r'channel_id=(UC[a-zA-Z0-9_-]{22})'),
    # Fallback: most frequent UC* string in the page is usually the channel itself
]


def normalise_url(arg: str) -> str:
    arg = arg.strip()
    if arg.startswith("http://") or arg.startswith("https://"):
        return arg
    if arg.startswith("@"):
        return f"https://www.youtube.com/{arg}"
    return f"https://www.youtube.com/@{arg}"


def fetch_page(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} fetching {url}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error: {e.reason}")


def find_channel_id(html: str) -> str | None:
    # Try explicit named patterns first
    for pat in SEARCH_PATTERNS[:-1]:
        m = pat.search(html)
        if m:
            return m.group(1)

    # Fallback: count occurrences of each UC* string and pick the most common
    counts: dict[str, int] = {}
    for m in CHANNEL_ID_RE.finditer(html):
        cid = m.group(1)
        counts[cid] = counts.get(cid, 0) + 1

    if counts:
        return max(counts, key=lambda k: counts[k])

    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    url = normalise_url(sys.argv[1])
    print(f"Fetching  : {url}")

    html = fetch_page(url)
    cid  = find_channel_id(html)

    if cid:
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        print(f"Channel ID: {cid}")
        print(f"RSS URL   : {rss_url}")
        print()
        print("Add to channels.yaml:")
        # Derive a friendly name from the URL argument
        handle = sys.argv[1].lstrip("@").split("/")[-1]
        print(f"  - name: {handle}")
        print(f"    id:   {cid}")
    else:
        print("Could not extract a channel ID automatically.")
        print("Try: open the channel page in your browser, View Source,")
        print('and search for "channelId" or "externalId".')


if __name__ == "__main__":
    main()
