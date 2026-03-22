---
name: fathom-hello-world
description: |
  Retrieve meeting transcripts and summaries from the Fathom API.
  Use when fetching meeting data, testing API access,
  or learning Fathom API response structure.
  Trigger with phrases like "fathom hello world", "fathom first api call",
  "get fathom transcript", "fathom meeting data".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Hello World

## Overview

First API calls against Fathom: list meetings, get a transcript, retrieve AI-generated summaries and action items.

## Prerequisites

- Completed `fathom-install-auth` setup
- At least one recorded meeting in Fathom

## Instructions

### Step 1: List Meetings

```bash
curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/meetings?limit=5" \
  | jq '.meetings[] | {id, title, created_at, duration_seconds}'
```

### Step 2: Get Meeting Transcript

```bash
RECORDING_ID="your-recording-id"

curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/recordings/${RECORDING_ID}/transcript" \
  | jq '.segments[] | {speaker, text, start_time}'
```

### Step 3: Get AI Summary and Action Items

```bash
# Get meeting with summary included
curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/meetings?include_summary=true&limit=1" \
  | jq '.meetings[0] | {title, summary, action_items}'
```

### Step 4: Filter Meetings by Date

```bash
# Meetings from the last 7 days
curl -s -H "X-Api-Key: ${FATHOM_API_KEY}" \
  "https://api.fathom.ai/external/v1/meetings?created_after=2026-03-15T00:00:00Z&limit=20" \
  | jq '.meetings | length'
```

## Output

- List of meetings with IDs and metadata
- Full transcript with speaker labels and timestamps
- AI-generated summary and action items

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Empty meetings array | No recordings in account | Record a meeting in Fathom |
| `404` on recording ID | Wrong ID or deleted | List meetings to get valid IDs |
| No summary available | Meeting still processing | Wait a few minutes after recording |
| Transcript empty | Recording too short | Minimum meeting length required |

## Resources

- [Fathom API Reference](https://developers.fathom.ai/api-reference)
- [Get Transcript](https://developers.fathom.ai/api-reference/recordings/get-transcript)

## Next Steps

Proceed to `fathom-local-dev-loop` for development workflow setup.
