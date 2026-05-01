---
name: web-research
description: "Use when extracting article text from news URLs or downloading video or audio with metadata"
allowed-tools: [Bash(python3*), Bash(yt-dlp*), Read]
version: 1.0.0
author: ykotik
license: MIT
---

# Web Research

## When to Use
- Extracting clean article text and metadata from a news/blog URL
- Downloading video or audio from supported sites with full metadata
- Getting video/audio metadata without downloading the media

## Tools

| Tool | Purpose | Structured output |
|------|---------|-------------------|
| **newspaper4k** | Extract article text, title, authors, date from URLs | Python object (access `.title`, `.text`, `.authors`) |
| **yt-dlp** | Download video/audio from 1000+ sites | `--dump-json` for metadata JSON |

## Patterns

### Extract article text from a URL
```bash
python3 -c "
from newspaper import Article
a = Article('https://example.com/news/article')
a.download()
a.parse()
import json
print(json.dumps({'title': a.title, 'authors': a.authors, 'date': str(a.publish_date), 'text': a.text[:2000]}, indent=2))
"
```

### Extract multiple articles
```bash
for url in "https://example.com/article1" "https://example.com/article2"; do
  python3 -c "
from newspaper import Article
import json
a = Article('$url')
a.download()
a.parse()
print(json.dumps({'url': '$url', 'title': a.title, 'text': a.text[:1000]}))
"
done
```

### Get video metadata without downloading
```bash
yt-dlp --dump-json "https://www.youtube.com/watch?v=VIDEO_ID" | jq '{title, duration, view_count, upload_date}'
```

### Download audio only (best quality)
```bash
yt-dlp -x --audio-format mp3 "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download video (best quality, specific format)
```bash
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]" "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Download with metadata and subtitles
```bash
yt-dlp --write-info-json --write-subs --sub-langs en "https://www.youtube.com/watch?v=VIDEO_ID"
```

### List available formats for a video
```bash
yt-dlp -F "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Pipelines

### Get video metadata → query with DuckDB
```bash
yt-dlp --dump-json "https://www.youtube.com/@channel/videos" --flat-playlist | head -20 > videos.jsonl
duckdb -c "SELECT title, view_count, duration FROM read_json_auto('videos.jsonl') ORDER BY view_count DESC LIMIT 10"
```
Each stage: yt-dlp dumps playlist metadata as JSONL, DuckDB queries for top videos by views.

## Prefer Over
- Prefer **newspaper4k** over curl + HTML parsing for article extraction — handles boilerplate removal, metadata extraction automatically
- Prefer **yt-dlp** over browser downloads — supports 1000+ sites, can extract metadata without downloading

## Do NOT Use When
- Need to interact with a web page (click, scroll, fill forms) — use web-crawling skill (Playwright)
- Real-time search with the WebSearch tool available — prefer the built-in tool for conversational search
- Downloading copyrighted content without authorization
- Target site requires authentication — use web-crawling skill with login automation
