---
name: tweetclaw
description: |
  X/Twitter automation plugin. Post tweets, reply, like, retweet, follow, unfollow, send DMs, search tweets, look up users, extract bulk data, monitor accounts, run giveaway draws, and compose algorithm-optimized tweets via Xquik REST API. Use when the user asks about Twitter, X, tweets, followers, social media automation, tweet analytics, or giveaway management. Trigger with "post tweet", "search tweets", "extract followers", "run giveaway", "monitor account", "compose tweet", "trending topics".
allowed-tools: "Read, Bash(curl:*), WebFetch"
version: "1.5.3"
author: "Burak Bayir <burak@xquik.com>"
license: "MIT"
compatible-with: claude-code, codex, openclaw
tags: [twitter, x, automation, social-media, giveaway, monitoring, scraping, mcp]
---

# TweetClaw

## Overview

TweetClaw provides full X/Twitter automation via the Xquik REST API. It covers 121 endpoints across 12 categories: tweet operations, user lookups, search, bulk extractions (23 tools), giveaway draws, account monitoring, webhook delivery, AI composition, style analysis, drafts, write actions, and account management.

Two MCP tools are available via the hosted server at `xquik.com/mcp` (not bundled with this plugin). See the MCP setup section in Resources for configuration instructions.

## Prerequisites

- An API key from [xquik.com](https://xquik.com) (starts with `xq_`)
- Set `XQUIK_API_KEY` environment variable or configure via OpenClaw:
  ```bash
  openclaw config set plugins.entries.tweetclaw.config.apiKey "$XQUIK_API_KEY"
  ```

## Instructions

### Reading Data

Search tweets, fetch user profiles, get timelines, bookmarks, notifications, DM history, and trending topics.

```bash
# Search tweets
curl -H "x-api-key: $XQUIK_API_KEY" \
  "https://xquik.com/api/v1/x/tweets/search?query=AI+agents&count=20"

# Get user profile
curl -H "x-api-key: $XQUIK_API_KEY" \
  "https://xquik.com/api/v1/x/users/elonmusk"

# Get tweet by ID
curl -H "x-api-key: $XQUIK_API_KEY" \
  "https://xquik.com/api/v1/x/tweets/1234567890"
```

### Writing Data

Post tweets, delete tweets, like/unlike, retweet, follow/unfollow, send DMs, update profile, upload media.

```bash
# Post a tweet
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello from TweetClaw!"}' \
  "https://xquik.com/api/v1/x/tweets"

# Like a tweet
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  "https://xquik.com/api/v1/x/tweets/1234567890/like"

# Follow a user (requires numeric user ID)
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  "https://xquik.com/api/v1/x/users/44196397/follow"
```

### Bulk Extractions

23 extraction tools for replies, quotes, retweets, followers, following, mentions, community members, list members, space participants, and more. Always estimate before extracting.

```bash
# Estimate extraction cost
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type": "reply_extractor", "params": {"tweetId": "1234567890"}}' \
  "https://xquik.com/api/v1/extractions/estimate"

# Create extraction
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"type": "reply_extractor", "params": {"tweetId": "1234567890"}}' \
  "https://xquik.com/api/v1/extractions"

# Retrieve results (poll status first)
curl -H "x-api-key: $XQUIK_API_KEY" \
  "https://xquik.com/api/v1/extractions/{id}/results"
```

### Giveaway Draws

Run auditable draws from tweet replies with filters (retweet required, follow check, min followers, account age, language, keywords).

```bash
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "tweetUrl": "https://x.com/handle/status/1234567890",
    "winnerCount": 3,
    "filters": {"mustRetweet": true, "mustFollow": "handle", "minFollowers": 10}
  }' \
  "https://xquik.com/api/v1/draws"
```

### Account Monitoring

Monitor X accounts for new tweets, follows, unfollows. Deliver events via webhook or Telegram.

```bash
# Create monitor
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"username": "openai"}' \
  "https://xquik.com/api/v1/monitors"

# Create webhook
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/webhook", "events": ["tweet.new"]}' \
  "https://xquik.com/api/v1/webhooks"
```

### AI Composition

Compose algorithm-optimized tweets with scoring, refinement, and style analysis.

```bash
curl -X POST -H "x-api-key: $XQUIK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"step": "compose", "topic": "AI productivity", "tone": "professional"}' \
  "https://xquik.com/api/v1/compose"
```

## Output

All endpoints return JSON. Successful responses include the requested data. Errors return `{"error": "error_code"}`.

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Process response |
| 400 | Invalid request | Fix parameters |
| 401 | Unauthenticated | Check API key |
| 402 | Billing issue | Subscribe or add credits |
| 404 | Not found | Resource does not exist |
| 429 | Rate limited | Retry with backoff |
| 5xx | Server error | Retry with backoff |

## Error Handling

- Retry only 429 and 5xx (max 3 retries, exponential backoff). Never retry other 4xx.
- Rate limits are per method tier: Read (120/60s), Write (30/60s), Delete (15/60s).
- Follow/DM endpoints require numeric user IDs, not usernames. Look up the user first via `GET /x/users/{username}`.
- Extraction IDs are strings (bigints that overflow JavaScript Number). Always treat as strings.
- Webhook secrets are shown only once at creation. Store immediately.
- Cursors are opaque. Never decode or construct `nextCursor` values.
- Always estimate before extracting to avoid 402 errors mid-extraction.

## Examples

### Full workflow: search, analyze, and compose

1. Search tweets: `GET /x/tweets/search?query=AI+agents&count=50`
2. Analyze engagement: Check likes, retweets, reply counts in results
3. Compose optimized tweet: `POST /compose` with topic and tone
4. Score the draft: `POST /compose` with `step: "score"`
5. Post the tweet: `POST /x/tweets` with the final text

### Full workflow: giveaway draw

1. Create draw: `POST /draws` with tweet URL and filters
2. Poll status: `GET /draws/{id}` until `status: "completed"`
3. Export results: `GET /draws/{id}/export?format=csv`

## Resources

- [Xquik API docs](https://docs.xquik.com)
- [TweetClaw source](https://github.com/Xquik-dev/tweetclaw)
- [Pricing details](https://docs.xquik.com/guides/billing)
- [MCP server setup](https://docs.xquik.com/mcp/overview)
