# Comment Funnel — Upload-Post Skill

AI agent skill for building Instagram comment-to-DM funnels via the Upload-Post API.

A creator posts "Comment GUIDE to get my free PDF" → people comment → the AI agent sends each commenter a personalized DM with the link. Automatically.

## What It Does

- Monitors comments on Instagram posts for trigger keywords
- Uses semantic matching (not just exact keywords) to detect intent
- Sends personalized private DMs to matching commenters
- Tracks who's been contacted to avoid duplicates
- Optionally monitors DM replies for follow-up conversations
- Reports funnel metrics (comments scanned, DMs sent, replies received)

## Supported Platforms

| Platform | Comments | Private Reply (DM) | Follow-up DMs |
|----------|----------|--------------------|---------------|
| Instagram | ✓ | ✓ | ✓ |

Instagram only — this is a Meta API limitation, not Upload-Post.

## Installation

### Claude Code / skills.sh

```bash
npx skills add Upload-Post/upload-post-comment-funnel
```

### Manual

Copy `SKILL.md` and `references/` to your agent's skills directory.

## Setup

1. Create account at [upload-post.com](https://upload-post.com)
2. Connect your Instagram Business account
3. Create a **Profile** (links your connected accounts)
4. Generate an **API Key** from the dashboard

## Usage Example

Tell your AI agent:

> "Set up a comment funnel on https://instagram.com/p/ABC123 — anyone who comments GUIDE gets a DM with the download link https://example.com/guide"

The agent will:
1. Start a persistent monitor on that post
2. Filter comments containing "guide" (case and accent insensitive)
3. Send each matching commenter a DM with the link
4. Keep monitoring every 15 minutes, auto-stops after 15 days

## Compliance

This skill uses Meta's official [Private Replies API](https://developers.facebook.com/docs/instagram-platform/private-replies/). It's the same mechanism used by ManyChat, Inro, and every major DM automation platform. See `references/compliance.md` for full details.

## Documentation

- Upload-Post API docs: https://docs.upload-post.com
- LLM-friendly reference: https://docs.upload-post.com/llm.txt

## License

MIT
