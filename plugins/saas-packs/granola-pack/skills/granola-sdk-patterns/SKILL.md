---
name: granola-sdk-patterns
description: |
  Zapier automation patterns and Enterprise API integration for Granola.
  Use when building automated workflows, connecting Granola to 8,000+ apps via Zapier,
  or querying the Enterprise API for notes and transcripts.
  Trigger: "granola zapier", "granola automation", "granola API", "granola SDK".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, automation, api]

---
# Granola SDK Patterns

## Overview
Granola does not have a traditional SDK. Integration is achieved through three channels: Zapier (8,000+ app connections), the Enterprise API (REST, workspace-level read access), and native integrations (Slack, Notion, HubSpot, Attio, Affinity). This skill covers automation patterns for all three.

## Prerequisites
- Granola Business plan ($14/user/month) for Zapier + native CRM
- Enterprise plan ($35+/user/month) for API access
- Zapier account for automation workflows

## Instructions

### Step 1 — Understand Zapier Triggers

Granola provides two Zapier triggers:

| Trigger | Fires When | Use Case |
|---------|-----------|----------|
| **Note Added to Granola Folder** | A note is placed in a specific folder | Auto-route by meeting type |
| **Note Shared to Zapier** | You manually share a note to Zapier | Selective sharing for important meetings |

**Webhook payload data available:**
- `title` — meeting title from calendar
- `creator_name` / `creator_email` — note creator
- `attendees[]` — array of `{name, email}` objects
- `calendar_event_title` — original calendar event name
- `calendar_event_datetime` — meeting date/time
- `note_content` — the enhanced note content (Markdown)

### Step 2 — Build Common Zap Patterns

**Pattern 1: Meeting Notes to Notion (auto-archive)**
```yaml
Trigger: Note Added to Granola Folder ("All Meetings")
Action: Notion — Create Database Item
  Database: Meeting Archive
  Title: "{{title}}"
  Date: "{{calendar_event_datetime}}"
  Content: "{{note_content}}"
  Attendees: "{{attendees}}"
```

**Pattern 2: Action Items to Asana/Linear**
```yaml
Trigger: Note Shared to Zapier
Filter: note_content contains "Action Items"
Code Step (JavaScript):
  const lines = inputData.note_content.split('\n');
  const actions = lines
    .filter(l => l.match(/^- \[ \]/))
    .map(l => l.replace('- [ ] ', ''));
  output = actions.map(a => ({task: a}));
Action: Linear — Create Issue (for each action)
  Title: "{{task}}"
  Team: Engineering
  Label: "meeting-action"
```

**Pattern 3: Sales Call Summary to Slack + HubSpot**
```yaml
Trigger: Note Added to Granola Folder ("Sales Calls")
Path A — Slack:
  Action: Post Message to #sales-updates
  Message: |
    *New Sales Call:* {{title}}
    *Attendees:* {{attendees}}

    {{note_content}}

    [View full notes in Granola]

Path B — HubSpot (via Zapier if not using native):
  Action: Find Contact by Email ({{attendees[0].email}})
  Action: Create Engagement Note
    Body: "{{note_content}}"
```

**Pattern 4: Meeting Follow-Up Email**
```yaml
Trigger: Note Shared to Zapier
Action: ChatGPT — Generate Follow-Up Email
  Prompt: "Write a professional follow-up email based on: {{note_content}}"
Action: Gmail — Create Draft
  To: "{{attendees}}"
  Subject: "Follow-up: {{title}}"
  Body: "{{chatgpt_response}}"
Action: Slack — Notify
  Message: "Follow-up draft ready for: {{title}}"
```

### Step 3 — Use the Enterprise API

Available on Enterprise plan. API keys generated at Settings > API Keys (up to 5 per workspace).

```bash
# List all accessible notes (paginated)
curl -s "https://api.granola.ai/v0/notes" \
  -H "Authorization: Bearer $GRANOLA_API_KEY" \
  -H "Content-Type: application/json" | jq '.notes[:3]'

# Get a specific note with transcript
curl -s "https://api.granola.ai/v0/notes/{note_id}" \
  -H "Authorization: Bearer $GRANOLA_API_KEY" | jq '{title, summary, action_items}'
```

**API characteristics:**
- Bearer token authentication
- Read-only access to publicly shared notes within your workspace
- Rate limited per workspace (429 response when exceeded)
- Pagination for list endpoints

**Reverse-engineered endpoints (unofficial, for reference):**
```
POST https://api.granola.ai/v2/get-documents    # List documents (paginated)
POST https://api.granola.ai/v1/get-document-transcript  # Get transcript
POST https://api.granola.ai/v1/get-workspaces    # List workspaces
POST https://api.granola.ai/v1/get-documents-batch  # Bulk fetch by IDs
```
Authentication uses WorkOS with refresh token rotation via `POST https://api.workos.com/user_management/authenticate`.

### Step 4 — Multi-Step Automation Chains

```yaml
Name: Complete Meeting Follow-Up Pipeline

Step 1 — Trigger:
  Granola: Note Added to Folder ("Client Meetings")

Step 2 — Filter:
  Only continue if attendees contain external email domains

Step 3 — Action:
  ChatGPT: Generate structured summary and follow-up email

Step 4 — Action:
  Gmail: Create draft follow-up email to external attendees

Step 5 — Action:
  Notion: Create page in Client Meeting Log database

Step 6 — Action:
  Linear: Create issues from action items with "client" label

Step 7 — Action:
  Slack: Post summary to #client-updates channel

Step 8 — Action:
  HubSpot: Log meeting note on matched Contact/Deal
```

### Step 5 — Folder-Based Routing

Organize Granola folders to drive different Zap behaviors:

| Folder | Zapier Trigger | Actions |
|--------|---------------|---------|
| `Sales Calls` | Auto | Slack #sales + HubSpot + follow-up email |
| `Engineering` | Auto | Linear tasks + Notion wiki |
| `All Hands` | Auto | Slack #general + Google Drive archive |
| `Interviews` | Manual share | Greenhouse scorecard + hiring panel Slack |
| `1-on-1s` | None | Private, no automation |

## Output
- Zapier workflows configured for automated note processing
- API access established for custom integrations
- Multi-step automation chains routing by meeting type
- Folder-based routing strategy implemented

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Zapier trigger not firing | Folder trigger misconfigured | Verify the exact folder name in Zapier matches Granola |
| Missing note content | Note still processing | Add a 2-minute delay step at the start of the Zap |
| API 429 Too Many Requests | Rate limit exceeded | Add delays between requests, implement backoff |
| API 401 Unauthorized | Invalid or expired API key | Regenerate key at Settings > API Keys |
| Attendee data empty | Calendar event has no attendee list | Add attendees to the calendar event |

## Resources
- [Zapier Granola App](https://zapier.com/apps/granola/integrations)
- [Automate Granola (4 Ways)](https://zapier.com/blog/automate-granola/)
- [Granola Enterprise API](https://docs.granola.ai/introduction)
- [Enterprise API Docs](https://docs.granola.ai/help-center/sharing/integrations/enterprise-api)

## Next Steps
Proceed to `granola-common-errors` for troubleshooting.
