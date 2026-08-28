---
name: upload-post
description: "Publish and schedule content to 15 social platforms through one Upload-Post API call: TikTok, Instagram, YouTube, LinkedIn, Facebook, X, Threads, Pinterest, Bluesky, Reddit, Discord, Telegram, Mastodon, WordPress and Google Business Profile. Use when posting or scheduling videos, photo carousels, text or documents across several platforms at once, checking upload status, or pulling analytics."
allowed-tools: Read, Write, Bash(curl:*), Bash(jq:*)
version: "1.1.0"
author: Upload-Post <support@upload-post.com>
license: MIT
compatibility: "Designed for Claude Code; works in any agent runtime supporting the Anthropic skill spec. Requires curl on PATH and an UPLOAD_POST_API_KEY. No local media tooling needed — uploads are server-side."
tags:
- social-media
- publishing
- scheduling
- api
- analytics
---

# Upload-Post API

Post content to multiple social media platforms with a single API call.

## Overview

One request fans out to every target platform and reports a per-platform result. Accounts are
connected once through OAuth in the Upload-Post dashboard, so this skill never handles
per-platform developer apps, review processes or token refresh — a single API key covers all
15 platforms.

Four content types are supported: video, photo carousels, text-only posts and documents
(LinkedIn). Each can be published immediately, scheduled for a future date, or added to a
posting queue.

## Documentation

- Full API docs: https://docs.upload-post.com
- LLM-friendly: https://docs.upload-post.com/llm.txt

## Setup

1. Create account at [upload-post.com](https://upload-post.com)
2. Connect your social media accounts
3. Create a **Profile** (e.g., "mybrand") - this links your connected accounts
4. Generate an **API Key** from dashboard
5. Use the profile name as `user` parameter in API calls

## Authentication

```
Authorization: Apikey YOUR_API_KEY
```

Base URL: `https://api.upload-post.com/api`

The `user` parameter in all endpoints refers to your **profile name** (not username), which determines which connected social accounts receive the content.

## Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload videos |
| `/upload_photos` | POST | Upload photos/carousels |
| `/upload_text` | POST | Text-only posts |
| `/upload_document` | POST | Upload documents (LinkedIn only) |
| `/uploadposts/status?request_id=X` | GET | Check async upload status |
| `/uploadposts/history` | GET | Upload history |
| `/uploadposts/schedule` | GET | List scheduled posts |
| `/uploadposts/schedule/<job_id>` | DELETE | Cancel scheduled post |
| `/uploadposts/schedule/<job_id>` | PATCH | Edit scheduled post |
| `/uploadposts/me` | GET | Validate API key |
| `/analytics/<profile>` | GET | Get analytics |
| `/uploadposts/facebook/pages` | GET | List Facebook pages |
| `/uploadposts/linkedin/pages` | GET | List LinkedIn pages |
| `/uploadposts/pinterest/boards` | GET | List Pinterest boards |
| `/uploadposts/reddit/detailed-posts` | GET | Get Reddit posts with media |
| `/ffmpeg` | POST | Process media with FFmpeg |

## Instructions

1. **Pick the endpoint** by content type — `/upload` for video, `/upload_photos` for photos
   and carousels, `/upload_text` for text-only, `/upload_document` for LinkedIn documents.
2. **Set `user`** to the profile name, not a social handle. The profile determines which
   connected accounts receive the content.
3. **Repeat `platform[]`** once per target platform.
4. **Add a `title`.** Required for YouTube and Reddit, optional everywhere else. Override it
   per platform with `<platform>_title` when the copy should differ.
5. **Set `async_upload=true`** for anything but the smallest files, then poll
   `/uploadposts/status?request_id=…` until it reaches a terminal state.
6. **Read the per-platform result** and report which platforms published and which failed —
   a request can partially succeed.

To schedule instead of publishing now, add `scheduled_date` (ISO-8601) and optionally
`timezone` (IANA). To let Upload-Post pick the next free slot, send `add_to_queue=true`.

## Upload Videos

```bash
curl -X POST "https://api.upload-post.com/api/upload" \
  -H "Authorization: Apikey YOUR_KEY" \
  -F "user=profile_name" \
  -F "platform[]=instagram" \
  -F "platform[]=tiktok" \
  -F "video=@video.mp4" \
  -F "title=My caption"
```

Key parameters:
- `user`: Profile username (required)
- `platform[]`: Target platforms (required)
- `video`: Video file or URL (required)
- `title`: Caption/title (required)
- `description`: Extended description
- `scheduled_date`: ISO-8601 date for scheduling
- `timezone`: IANA timezone (e.g., "Europe/Madrid")
- `async_upload`: Set `true` for background processing
- `first_comment`: Auto-post first comment

## Upload Photos

```bash
curl -X POST "https://api.upload-post.com/api/upload_photos" \
  -H "Authorization: Apikey YOUR_KEY" \
  -F "user=profile_name" \
  -F "platform[]=instagram" \
  -F "photos[]=@photo1.jpg" \
  -F "photos[]=@photo2.jpg" \
  -F "title=My caption"
```

Instagram & Threads support mixed carousels (photos + videos in same post).

## Upload Text

```bash
curl -X POST "https://api.upload-post.com/api/upload_text" \
  -H "Authorization: Apikey YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user": "profile_name",
    "platform": ["x", "threads", "bluesky"],
    "title": "My text post"
  }'
```

Supported: X, LinkedIn, Facebook, Threads, Reddit, Bluesky.

## Upload Document (LinkedIn only)

Upload PDFs, PPTs, DOCs as native LinkedIn document posts (carousel viewer).

```bash
curl -X POST "https://api.upload-post.com/api/upload_document" \
  -H "Authorization: Apikey YOUR_KEY" \
  -F "user=profile_name" \
  -F 'platform[]=linkedin' \
  -F "document=@presentation.pdf" \
  -F "title=Document Title" \
  -F "description=Post text above document"
```

Parameters:
- `document`: PDF, PPT, PPTX, DOC, DOCX (max 100MB, 300 pages)
- `title`: Document title (required)
- `description`: Post commentary
- `visibility`: PUBLIC, CONNECTIONS, LOGGED_IN, CONTAINER
- `target_linkedin_page_id`: Post to company page

## Supported Platforms

| Platform | Videos | Photos | Text | Documents |
|----------|--------|--------|------|-----------|
| TikTok | ✓ | ✓ | - | - |
| Instagram | ✓ | ✓ | - | - |
| YouTube | ✓ | - | - | - |
| LinkedIn | ✓ | ✓ | ✓ | ✓ |
| Facebook | ✓ | ✓ | ✓ | - |
| X (Twitter) | ✓ | ✓ | ✓ | - |
| Threads | ✓ | ✓ | ✓ | - |
| Pinterest | ✓ | ✓ | - | - |
| Reddit | - | ✓ | ✓ | - |
| Bluesky | ✓ | ✓ | ✓ | - |

## Upload History

```bash
curl "https://api.upload-post.com/api/uploadposts/history?page=1&limit=20" \
  -H "Authorization: Apikey YOUR_KEY"
```

Parameters:
- `page`: Page number (default: 1)
- `limit`: 10, 20, 50, or 100 (default: 10)

Returns: upload timestamp, platform, success status, post URLs, errors.

## Scheduling

Add `scheduled_date` parameter (ISO-8601):

```json
{
  "scheduled_date": "2026-02-01T10:00:00Z",
  "timezone": "Europe/Madrid"
}
```

Response includes `job_id`. Manage with:
- `GET /uploadposts/schedule` - List all scheduled
- `DELETE /uploadposts/schedule/<job_id>` - Cancel
- `PATCH /uploadposts/schedule/<job_id>` - Edit (date, title, caption)

## Check Upload Status

For async uploads or scheduled posts:

```bash
curl "https://api.upload-post.com/api/uploadposts/status?request_id=XXX" \
  -H "Authorization: Apikey YOUR_KEY"
```

Or use `job_id` for scheduled posts.

## Analytics

```bash
curl "https://api.upload-post.com/api/analytics/profile_name?platforms=instagram,tiktok" \
  -H "Authorization: Apikey YOUR_KEY"
```

Supported: Instagram, TikTok, LinkedIn, Facebook, X, YouTube, Threads, Pinterest, Reddit, Bluesky.

Returns: followers, impressions, reach, profile views, time-series data.

## Get Pages/Boards

```bash
# Facebook Pages
curl "https://api.upload-post.com/api/uploadposts/facebook/pages" \
  -H "Authorization: Apikey YOUR_KEY"

# LinkedIn Pages  
curl "https://api.upload-post.com/api/uploadposts/linkedin/pages" \
  -H "Authorization: Apikey YOUR_KEY"

# Pinterest Boards
curl "https://api.upload-post.com/api/uploadposts/pinterest/boards" \
  -H "Authorization: Apikey YOUR_KEY"
```

## Reddit Detailed Posts

Get posts with full media info (images, galleries, videos):

```bash
curl "https://api.upload-post.com/api/uploadposts/reddit/detailed-posts?profile_username=myprofile" \
  -H "Authorization: Apikey YOUR_KEY"
```

Returns up to 2000 posts with media URLs, dimensions, thumbnails.

## FFmpeg Editor

Process media with custom FFmpeg commands:

```bash
curl -X POST "https://api.upload-post.com/api/ffmpeg" \
  -H "Authorization: Apikey YOUR_KEY" \
  -F "file=@input.mp4" \
  -F "full_command=ffmpeg -y -i {input} -c:v libx264 -crf 23 {output}" \
  -F "output_extension=mp4"
```

- Use `{input}` and `{output}` placeholders
- Poll job status until `FINISHED`
- Download result from `/ffmpeg/job/<job_id>/download`
- Supports multiple inputs: `{input0}`, `{input1}`, etc.

Quotas: Free 30min/mo, Basic 300min, Pro 1000min, Advanced 3000min, Business 10000min.

## Platform-Specific Parameters

See [references/platforms.md](references/platforms.md) for detailed platform parameters.

## Media Requirements

See [references/requirements.md](references/requirements.md) for format specs per platform.

## Output

An accepted upload returns a `request_id`. With `async_upload=true` the platforms are still
processing at that point:

```json
{ "success": true, "request_id": "req_8f21c04a" }
```

Polling `/uploadposts/status?request_id=…` returns the per-platform outcome. Report each
platform separately — a request can partially succeed:

```json
{
  "status": "completed",
  "results": {
    "tiktok":    { "success": true,  "post_url": "https://tiktok.com/@brand/video/7412..." },
    "instagram": { "success": true,  "post_url": "https://instagram.com/reel/C8xY2..." },
    "youtube":   { "success": false, "error_code": "quota_exceeded" }
  }
}
```

A scheduled post responds `202` with a `job_id` instead, which later appears in upload history.

## Examples

**Publish a clip to three platforms with platform-specific captions**

```bash
curl -X POST "https://api.upload-post.com/api/upload" \
  -H "Authorization: Apikey $UPLOAD_POST_API_KEY" \
  -F "user=mybrand" \
  -F "platform[]=tiktok" -F "platform[]=instagram" -F "platform[]=youtube" \
  -F "video=@clip.mp4" \
  -F "title=How to build better habits" \
  -F "tiktok_title=the 1 habit that changed everything 🔥 #fyp" \
  -F "youtube_title=How To Build Better Habits (5 Minute Guide)" \
  -F "async_upload=true"
```

**Schedule a carousel for next Monday, Madrid time**

```bash
curl -X POST "https://api.upload-post.com/api/upload_photos" \
  -H "Authorization: Apikey $UPLOAD_POST_API_KEY" \
  -F "user=mybrand" -F "platform[]=instagram" \
  -F "photos[]=@slide1.jpg" -F "photos[]=@slide2.jpg" \
  -F "title=Five lessons from year one" \
  -F "scheduled_date=2026-09-01T09:00:00Z" -F "timezone=Europe/Madrid"
```

**Retry only the platforms that failed**

```bash
curl -X POST "https://api.upload-post.com/api/upload" \
  -H "Authorization: Apikey $UPLOAD_POST_API_KEY" \
  -F "user=mybrand" -F "video=@clip.mp4" -F "title=..." \
  -F "retry_request_id=req_8f21c04a"
```

## Error Handling

| Code | Meaning |
|------|---------|
| 400 | Bad request / missing params |
| 401 | Invalid API key |
| 404 | Resource not found |
| 429 | Rate limit / quota exceeded |
| 500 | Server error |

The failure modes that actually bite:

- **`401 Invalid or expired token` with a key you know is good** — the key was sent as
  `Bearer`. API keys use the `Apikey` scheme. The message is misleading: the key is fine,
  the scheme is wrong.
- **Some platforms succeeded, others failed** — this is normal, not an exception. Read
  `results` per platform and retry only the failures with `retry_request_id` instead of
  re-uploading everything.
- **The request timed out** — uploads longer than 59 seconds switch to async automatically.
  Do not treat a timeout as a failure; poll `/uploadposts/status` with the `request_id`.
- **`reached_active_user_cap` on TikTok** — TikTok's daily cap was hit. By default the video
  falls back to the TikTok inbox as a draft: `success` is still `true`, the result carries
  `fallback_to_inbox: true`, and the id starts with `v_inbox_file`. The video is waiting in
  the app, not live.
- **Missing title on YouTube or Reddit** — both reject the upload; every other platform
  accepts an empty title.
- **Duplicate posts after a retry** — send an `Idempotency-Key` header. A retried request
  with a matching key returns the existing job rather than publishing twice.

## Notes

- Videos auto-switch to async if >59s processing time
- X long text creates threads unless `x_long_text_as_post=true`
- Facebook requires Page ID (personal profiles not supported by Meta)
- Instagram/Threads support mixed carousels (photos + videos)

## Resources

- API documentation: https://docs.upload-post.com
- LLM-friendly dump: https://docs.upload-post.com/llm.txt
- Platform-specific parameters: [references/platforms.md](references/platforms.md)
- Media format requirements: [references/requirements.md](references/requirements.md)
- Dashboard and API keys: https://upload-post.com
- MCP connector: https://mcp.upload-post.com/mcp
