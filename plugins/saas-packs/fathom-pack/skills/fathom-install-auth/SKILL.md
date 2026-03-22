---
name: fathom-install-auth
description: |
  Configure Fathom AI meeting assistant API access with API key authentication.
  Use when setting up Fathom API integration, generating API keys,
  or configuring webhook access for meeting data.
  Trigger with phrases like "install fathom", "setup fathom api",
  "fathom auth", "fathom api key", "configure fathom".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Install & Auth

## Overview

Set up Fathom AI API access for retrieving meeting transcripts, summaries, and action items. The API at `api.fathom.ai/external/v1` uses `X-Api-Key` header authentication with per-user API keys.

## Prerequisites

- Fathom account (free or Team plan)
- API access enabled in Settings

## Instructions

### Step 1: Generate API Key

1. Log in to https://fathom.video
2. Navigate to **Settings** > **Integrations** > **API Access**
3. Click **Generate API Key**
4. Copy and store the key securely

```bash
export FATHOM_API_KEY="your-api-key-here"

# Verify the key works
curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  https://api.fathom.ai/external/v1/meetings?limit=1 | jq .
```

### Step 2: Configure Environment

```bash
# .env -- NEVER commit
FATHOM_API_KEY=your-api-key
FATHOM_BASE_URL=https://api.fathom.ai/external/v1

# .gitignore
.env
.env.local
```

### Step 3: Test API Connectivity

```bash
# List recent meetings
curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/meetings?limit=5" \
  | jq '.meetings[] | {id: .id, title: .title, date: .created_at}'
```

### Step 4: OAuth Setup (For Public Apps)

```bash
# For building integrations others will use, register an OAuth app
# at developers.fathom.ai for marketplace listing eligibility

# OAuth apps cannot use include_transcript or include_summary
# in list requests -- use individual recording endpoints instead
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Regenerate in Settings > API Access |
| `403 Forbidden` | Key lacks access | API keys access your meetings + team shared |
| `429 Too Many Requests` | Rate limit (60/min) | Implement backoff |
| Empty meetings list | No recordings yet | Record a meeting first |

## Resources

- [Fathom API Docs](https://developers.fathom.ai)
- [Fathom API Quickstart](https://developers.fathom.ai/quickstart)
- [Fathom Help Center](https://help.fathom.video/en/articles/8368641)

## Next Steps

Proceed to `fathom-hello-world` to retrieve your first meeting transcript.
