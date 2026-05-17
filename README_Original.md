# YouTube Trailer RSS Feed

Automatically aggregates film trailers from YouTube studio channels into a single RSS feed, hosted free on GitHub Pages and consumed by any RSS reader (e.g. Thunderbird).

## How it works

1. A Python script fetches YouTube's native Atom feed for each channel you configure.
2. It filters entries whose titles contain `trailer` or `teaser` (configurable).
3. A combined RSS 2.0 file is written to `docs/feed.xml`.
4. A GitHub Action runs every 2 hours, regenerates the feed, and commits the result.
5. GitHub Pages serves `docs/feed.xml` at a permanent public URL.
6. Your RSS reader polls that URL.

YouTube provides a native Atom feed for every channel at:
```
https://www.youtube.com/feeds/videos.xml?channel_id=UC...
```
No API key or quota is needed.

---

## Setup

### 1. Create the GitHub repository

1. Create a new **public** repository on GitHub (e.g. `youtube-trailer-rss`).
2. Clone it locally.

### 2. Add the files

Copy these files into the root of your repo:

```
youtube-trailer-rss/
├── .github/
│   └── workflows/
│       └── generate-feed.yml   ← GitHub Actions workflow
├── generate_feed.py            ← main script
├── find_channel_id.py          ← helper: look up channel IDs
├── channels.yaml               ← your channel list and config
├── docs/                       ← created automatically on first run
│   └── feed.xml
└── README.md
```

Commit and push everything.

### 3. Find your channel IDs

YouTube channel IDs look like `UCVjsbqKtxkLt7bal4NHdgZA`.  
Run the helper for each channel you want to follow:

```bash
python find_channel_id.py @A24
python find_channel_id.py @WarnerBrosPictures
python find_channel_id.py @Netflix
# etc.
```

Each command prints the channel ID and the exact YAML snippet to paste into `channels.yaml`.

### 4. Edit channels.yaml

Fill in the `id:` field for each channel. Add or remove channels freely.  
Change `filter_keywords` if you also want clips, featurettes, etc.

Don't forget to update `feed_link` with your actual GitHub Pages URL (see step 6).

### 5. Enable GitHub Pages

1. Push your changes to GitHub.
2. Go to your repo → **Settings** → **Pages**.
3. Under *Build and deployment*, set:
   - **Source**: Deploy from a branch
   - **Branch**: `main`
   - **Folder**: `/docs`
4. Click **Save**.

GitHub Pages will be live at:
```
https://YOUR_USERNAME.github.io/youtube-trailer-rss/
```

### 6. Trigger the first run

Go to your repo → **Actions** → **Generate Film Trailer RSS Feed** → **Run workflow**.

After it completes, your feed will be at:
```
https://YOUR_USERNAME.github.io/youtube-trailer-rss/feed.xml
```

### 7. Subscribe in Thunderbird

1. In Thunderbird, go to **File → Subscribe to This Feed** (or right-click *Feeds* in the sidebar → *New Feed*).
2. Paste your feed URL.
3. Done. Thunderbird will poll it automatically.

---

## Customisation

| Setting | Where | Notes |
|---|---|---|
| Run frequency | `generate-feed.yml` → `cron` | Default: every 2 hours |
| Filter keywords | `channels.yaml` → `filter_keywords` | Add `"featurette"`, `"clip"`, etc. |
| Add/remove channels | `channels.yaml` → `channels` | Use `find_channel_id.py` to get IDs |
| Feed title/description | `channels.yaml` | Shown in your RSS reader |

## Notes

- YouTube's channel feeds only expose the **15 most recent videos**. Since studios don't post 15 trailers between your feed's update cycles, this is not a practical limitation.
- The `docs/feed.xml` file is committed to the repo on every change, so you can inspect its history.
- GitHub Actions free tier gives 2,000 minutes/month. Each run takes ~15 seconds, so 12 runs/day × 30 days = 360 minutes — well within the free limit.
- The `find_channel_id.py` script scrapes the channel page. If YouTube changes their page structure it may need updating; as a fallback, open the channel page, View Source, and search for `channelId`.
