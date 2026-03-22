---
name: fathom-core-workflow-a
description: |
  Build a meeting analytics pipeline with Fathom transcripts and summaries.
  Use when extracting insights from meetings, building CRM sync,
  or creating automated meeting follow-up workflows.
  Trigger with phrases like "fathom analytics", "fathom meeting pipeline",
  "fathom transcript analysis", "fathom action items sync".
allowed-tools: Read, Write, Edit, Bash(python3:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Core Workflow: Meeting Analytics

## Overview

Build automated meeting analytics: extract action items, sync to project management tools, analyze meeting patterns, and create follow-up workflows.

## Instructions

### Step 1: Batch Meeting Export

```python
from fathom_client import FathomClient
from datetime import datetime, timedelta

client = FathomClient()

# Get all meetings from last 7 days
week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat() + "Z"
meetings = client.list_meetings(
    limit=50,
    created_after=week_ago,
    include_summary="true",
)

for meeting in meetings:
    print(f"Meeting: {meeting['title']}")
    print(f"  Date: {meeting['created_at']}")
    print(f"  Summary: {meeting.get('summary', 'N/A')[:100]}...")
    for item in meeting.get("action_items", []):
        print(f"  Action: {item['text']} -> {item.get('assignee', 'unassigned')}")
    print()
```

### Step 2: Action Item Extraction Pipeline

```python
def extract_action_items(meetings: list[dict]) -> list[dict]:
    items = []
    for meeting in meetings:
        for action in meeting.get("action_items", []):
            items.append({
                "meeting_title": meeting["title"],
                "meeting_date": meeting["created_at"],
                "action_text": action["text"],
                "assignee": action.get("assignee", "unassigned"),
                "meeting_id": meeting["id"],
            })
    return items

# Sync to task tracker
def sync_to_linear(items: list[dict], api_key: str):
    for item in items:
        # Create Linear issue from action item
        pass
```

### Step 3: Meeting Pattern Analysis

```python
def analyze_meeting_patterns(meetings: list[dict]) -> dict:
    total = len(meetings)
    total_duration = sum(m.get("duration_seconds", 0) for m in meetings)
    total_actions = sum(len(m.get("action_items", [])) for m in meetings)

    return {
        "total_meetings": total,
        "total_hours": round(total_duration / 3600, 1),
        "avg_duration_min": round(total_duration / total / 60, 1) if total else 0,
        "total_action_items": total_actions,
        "avg_actions_per_meeting": round(total_actions / total, 1) if total else 0,
    }
```

## Resources

- [Fathom API Reference](https://developers.fathom.ai/api-reference)

## Next Steps

For CRM sync and webhook automation, see `fathom-core-workflow-b`.
