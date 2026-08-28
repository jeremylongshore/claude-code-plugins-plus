# Upload-Post Skill for Claude Code / AI Agents

A skill for AI agents (Claude Code, Clawdbot, etc.) to upload content to social media platforms via the Upload-Post API.

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

## Features

- Upload videos, photos, carousels, text posts, and documents
- Schedule posts for later
- Cross-post to multiple platforms simultaneously
- FFmpeg media processing (resize, transcode, etc.)
- Analytics retrieval
- Upload history tracking

## Installation

### For Claude Code / skills.sh
```bash
npx skills add Upload-Post/upload-post-skill
```

### Manual Installation
Copy `SKILL.md` and `references/` to your agent's skills directory.

## Setup

1. Create account at [upload-post.com](https://upload-post.com)
2. Connect your social media accounts
3. Create a **Profile** (links your connected accounts)
4. Generate an **API Key** from dashboard

## Usage

The skill provides comprehensive API documentation in `SKILL.md`. Your AI agent can:

```bash
# Upload a video
curl -X POST "https://api.upload-post.com/api/upload" \
  -H "Authorization: Apikey YOUR_KEY" \
  -F "user=profile_name" \
  -F "platform[]=instagram" \
  -F "platform[]=tiktok" \
  -F "video=@video.mp4" \
  -F "title=My caption"

# Upload photos
curl -X POST "https://api.upload-post.com/api/upload_photos" \
  -H "Authorization: Apikey YOUR_KEY" \
  -F "user=profile_name" \
  -F "platform[]=instagram" \
  -F "photos[]=@photo1.jpg" \
  -F "title=My caption"

# Check upload status
curl "https://api.upload-post.com/api/uploadposts/status?request_id=XXX" \
  -H "Authorization: Apikey YOUR_KEY"
```

## Documentation

- Full API docs: https://docs.upload-post.com
- LLM-friendly: https://docs.upload-post.com/llm.txt

## License

MIT
