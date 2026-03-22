---
name: granola-core-workflow-b
description: |
  Post-meeting note processing, sharing, and follow-up workflows in Granola.
  Use when enhancing notes after meetings, sharing to Slack/Notion/CRM,
  drafting follow-up emails, or processing action items.
  Trigger: "granola post-meeting", "share granola notes", "granola follow-up",
  "granola enhance", "granola share".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, workflow, sharing]

---
# Granola Core Workflow B: Post-Meeting Processing & Sharing

## Overview
After a meeting ends, Granola processes your audio and produces a transcript. This skill covers the post-meeting workflow: enhancing notes, sharing to integrations, using Granola Chat for follow-up, and managing the People & Companies CRM.

## Prerequisites
- At least one meeting captured in Granola
- Integrations connected (Slack, Notion, HubSpot — optional but recommended)
- Templates configured (see `granola-core-workflow-a`)

## Instructions

### Step 1 — Enhance Notes
After the meeting ends (transcript processing takes 1-2 minutes):

1. Open the meeting note in Granola
2. Click **Enhance Notes**
3. Select your template (or accept the auto-matched one)
4. Granola merges your typed notes + full transcript into structured output

The Enhance step uses GPT-4o or Claude to:
- Organize content under template sections
- Extract action items with owners
- Identify key decisions
- Generate a concise summary
- Pull verbatim quotes (if your template includes that section)

### Step 2 — Review and Edit
Before sharing, review the enhanced notes:

- [ ] Action items are correctly attributed to the right people
- [ ] Decisions are accurately captured
- [ ] No sensitive information in sections you plan to share externally
- [ ] Summary reflects the actual meeting outcome (not hallucinated)

Edit directly in the Granola editor — changes are saved instantly.

### Step 3 — Share to Integrations

**Slack (native integration):**
1. Click **Share** > **Slack**
2. Select the target channel (or use auto-post to a configured folder's default channel)
3. Granola posts a concise summary with action items
4. Recipients can click through to the full note or use **AI Chat** in Slack for questions

**Notion (native integration):**
1. Click **Share** > **Notion**
2. Notes are saved as rows in a dedicated Notion database (created on first connect)
3. Each note becomes a database entry with title, date, participants, and content
4. Currently one-at-a-time sharing (for auto-sync, use Zapier — see `granola-sdk-patterns`)

**HubSpot / Attio / Affinity (native CRM integration):**
1. Click **Share** > **HubSpot** (or Attio/Affinity)
2. Granola auto-matches the note to the correct Contact, Company, or Deal based on attendee emails
3. Review the match suggestion and confirm
4. Meeting summary appears on the CRM record timeline

> **Note:** Native HubSpot integration does not auto-create new contacts. Create the contact in HubSpot first, then sync the note. For automatic contact creation, use a Zapier workflow with a "Find or Create Contact" step.

### Step 4 — Use Granola Chat for Follow-Up

After enhancement, use the chat panel for post-meeting tasks:

```
You: "Draft a follow-up email to the client summarizing what we agreed"

Granola: Subject: Follow-up: Q1 Planning Discussion

Hi Sarah,

Thank you for the productive discussion today. Here's a summary
of what we agreed:

1. Timeline: MVP delivery by April 15
2. Budget: Approved up to $50K for Phase 1
3. Next Steps: Your team will share the API spec by Friday

Please let me know if I've missed anything.

Best regards
```

Other useful Chat queries:
- "What did [person] say about [topic]?" — searches transcript
- "List all open questions from this meeting" — finds unresolved items
- "Compare this meeting's decisions with last week's" — cross-note analysis
- "Create Jira ticket descriptions for each action item" — formatted for paste

### Step 5 — Manage People & Companies
After meetings, Granola automatically updates contact records:

1. Open **People** in the sidebar — see all contacts from meetings
2. Click a person to view their full meeting history with you
3. Open **Companies** for organization-level aggregation
4. Before a follow-up meeting, review the contact card to refresh context

This built-in CRM tracks:
- Meeting frequency per contact
- Last interaction date
- Full conversation history across all meetings
- Job titles and company info (auto-enriched)

### Step 6 — Organize with Folders
Structure your notes using folders:

| Folder | Purpose | Sharing |
|--------|---------|---------|
| `Sales Calls` | Client-facing meetings | Auto-post to #sales Slack |
| `Engineering` | Technical meetings | Share to Notion wiki |
| `Leadership` | Exec meetings | Private, no auto-share |
| `Interviews` | Hiring loops | Shared with hiring panel only |

Folders support auto-posting rules: any note added to a folder can automatically trigger Slack posts or Zapier workflows.

## Output
- Enhanced notes with structured sections, decisions, and action items
- Notes shared to Slack, Notion, and/or CRM as needed
- Follow-up email drafted via Granola Chat
- People & Companies records updated with meeting context

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Enhance produces poor output | Template too complex or meeting too short | Simplify template sections, ensure meeting > 5 min |
| Slack post missing | Channel not configured or bot not invited | Verify channel in Settings > Slack, invite Granola bot |
| HubSpot contact mismatch | Attendee email differs from CRM record | Update attendee email or CRM contact |
| Notion share fails | Authorization expired | Reconnect Notion in Settings > Integrations |
| Chat gives wrong answer | Ambiguous question | Be specific: "What did Sarah say about the timeline?" |

## Resources
- [Sharing and Integrations](https://docs.granola.ai/help-center/sharing/integrations/integrations-with-granola)
- [Granola + HubSpot](https://www.granola.ai/blog/granola-hubspot-integration-crm-updates)
- [Notion Integration](https://docs.granola.ai/help-center/sharing/notion)
- [People and Companies](https://docs.granola.ai/help-center/people-and-companies)

## Next Steps
Proceed to `granola-sdk-patterns` for Zapier automation and multi-app workflows.
