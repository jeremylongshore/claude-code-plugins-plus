---
name: fathom-core-workflow-b
description: |
  Sync Fathom meeting data to CRM and build automated follow-up workflows.
  Use when integrating Fathom with Salesforce, HubSpot, or custom CRMs,
  or creating automated post-meeting email summaries.
  Trigger with phrases like "fathom crm sync", "fathom salesforce",
  "fathom follow-up", "fathom post-meeting workflow".
allowed-tools: Read, Write, Edit, Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom Core Workflow: CRM Sync & Follow-Up

## Overview

Automate post-meeting workflows: sync meeting notes to CRM opportunities, send follow-up emails with action items, and maintain a meeting history database.

## Instructions

### Meeting-to-CRM Sync

```python
def sync_meeting_to_crm(meeting: dict, crm_client):
    summary = meeting.get("summary", "")
    action_items = meeting.get("action_items", [])
    participants = meeting.get("participants", [])

    # Find matching CRM contact/opportunity by participant email
    for email in participants:
        contact = crm_client.find_contact(email=email)
        if contact:
            crm_client.log_activity(
                contact_id=contact["id"],
                type="meeting",
                subject=meeting["title"],
                body=f"Summary: {summary}\n\nAction Items:\n" +
                     "\n".join(f"- {a['text']}" for a in action_items),
                date=meeting["created_at"],
            )
```

### Automated Follow-Up Email

```python
def generate_followup_email(meeting: dict) -> str:
    actions = meeting.get("action_items", [])
    action_list = "\n".join(f"- {a['text']}" for a in actions)

    return f"""Hi team,

Thanks for the meeting: {meeting['title']}

Summary:
{meeting.get('summary', 'No summary available')}

Action Items:
{action_list if action_list else '- None recorded'}

Best regards"""
```

### Meeting History Database

```sql
CREATE TABLE fathom_meetings (
    id VARCHAR PRIMARY KEY,
    title VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    duration_seconds INTEGER,
    summary TEXT,
    participant_count INTEGER,
    action_item_count INTEGER,
    synced_to_crm BOOLEAN DEFAULT FALSE,
    synced_at TIMESTAMP
);
```

## Resources

- [Fathom API Reference](https://developers.fathom.ai/api-reference)
- [Fathom Integrations](https://fathom.video/integrations)

## Next Steps

For error troubleshooting, see `fathom-common-errors`.
