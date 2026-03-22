---
name: granola-deploy-integration
description: |
  Deploy Granola native integrations — Slack, Notion, HubSpot, Attio, Affinity, and Zapier.
  Step-by-step setup for each platform with configuration, testing, and automation chains.
  Trigger: "granola slack", "granola notion", "granola hubspot",
  "granola attio", "connect granola", "granola integration".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, integrations, deployment]

---
# Granola Deploy Integration

## Overview
Granola offers native integrations with Slack, Notion, HubSpot, Attio, and Affinity plus Zapier for 8,000+ additional apps. This skill covers setup, configuration, and testing for each platform. Business plan ($14/user/mo) required for all integrations.

## Prerequisites
- Granola Business or Enterprise plan
- Admin access to target platforms (Slack workspace admin, Notion workspace, CRM portal)
- Integration requirements documented per team

## Instructions

### Integration 1 — Slack

**Setup:**
1. Settings (avatar bottom-left) > Integrations > **Slack** > Connect
2. Authorize Granola in your Slack workspace
3. Configure default channels per Granola folder:

| Granola Folder | Slack Channel | Auto-Post |
|---------------|--------------|-----------|
| Sales Calls | #sales-notes | On |
| Engineering | #eng-meetings | On |
| All Hands | #general | On |
| 1-on-1s | (none) | Off |

**How it works:**
- After enhancing notes, click **Share** > **Slack** > select channel
- With auto-post enabled on a folder, every note in that folder posts automatically
- Slack messages include a concise summary + action items
- Recipients can ask follow-up questions via the **AI Chat** button in Slack

**Slack Huddles support:**
Granola captures Slack Huddle audio the same way as Zoom/Meet — via system audio. Just ensure Granola is running and the huddle is on a synced calendar (or manually start recording).

### Integration 2 — Notion

**Setup:**
1. Settings > Integrations > **Notion** > Connect
2. Authorize Granola in your Notion workspace
3. Granola creates a dedicated database on first connection

**How it works:**
- Click **Share** > **Notion** to send a note
- Each note becomes a row in Granola's Notion database with:
  - Title, Date, Participants, Content (full enhanced note)
- You **cannot** choose a custom database — Granola creates its own
- Sharing is one-at-a-time (not automatic)

**Auto-sync workaround (via Zapier):**
```yaml
Trigger: Granola — Note Added to Folder ("All Meetings")
Action: Notion — Create Database Item
  Database: Your Custom Database
  Title: "{{title}}"
  Date: "{{calendar_event_datetime}}"
  Content: "{{note_content}}"
```
This bypasses the one-at-a-time limitation and lets you target any Notion database.

### Integration 3 — HubSpot (Native CRM)

**Setup:**
1. Settings > Integrations > **HubSpot** > Connect
2. Authorize Granola in your HubSpot portal
3. Granola auto-matches notes to Contacts, Companies, or Deals

**How it works:**
- After enhancing notes, click **Share** > **HubSpot**
- Granola suggests the matching Contact/Company/Deal based on attendee emails
- Review the match and confirm — the meeting summary appears on the CRM timeline
- Sync is **manual per note** (you choose which notes go to HubSpot)

**Limitations:**
- Does **not** auto-create new contacts (create in HubSpot first)
- No automatic bulk sync (use Zapier for that)
- Matching requires attendee emails to exist as HubSpot contacts

**Zapier auto-sync workaround:**
```yaml
Trigger: Granola — Note Added to Folder ("Sales Calls")
Action: HubSpot — Find Contact (by attendee email)
Action: HubSpot — Create Contact (if not found)
Action: HubSpot — Create Engagement Note on Contact
  Body: "{{note_content}}"
```

### Integration 4 — Attio (Native CRM)

**Setup:**
1. Settings > Integrations > **Attio** > Connect
2. Granola automatically matches notes to the right Person, Company, or Deal
3. Notes appear on Attio record timelines

Attio integration works similarly to HubSpot — manual sync per note, auto-matching by attendee email.

### Integration 5 — Affinity (Native CRM)

**Setup:**
1. Settings > Integrations > **Affinity** > Connect
2. Authorize access
3. Notes sync to matched Affinity records

### Integration 6 — Zapier (8,000+ Apps)

**Setup:**
1. Create a Zapier account at zapier.com
2. Search for "Granola" in the Zapier app directory
3. Connect your Granola account via OAuth

**Available triggers:**
| Trigger | Description |
|---------|-------------|
| Note Added to Granola Folder | Auto-fires when any note is added to a specific folder |
| Note Shared to Zapier | Fires when you manually share a note to Zapier |

**Popular Zapier recipes:**
| Recipe | Trigger → Action |
|--------|-----------------|
| Notes to Google Drive | Note Added → Google Drive: Upload File |
| Action items to Asana | Note Shared → Asana: Create Task |
| Summary to email | Note Added → Gmail: Send Email |
| Notes to Salesforce | Note Shared → Salesforce: Create Note |
| Digest to Teams | Note Added → Microsoft Teams: Post Message |

### Multi-Integration Workflow

Deploy a complete meeting follow-up chain:

```
Meeting ends → Granola enhances notes
  → Note added to "Client Meetings" folder
    ├→ Slack: Post summary to #client-updates
    ├→ Notion: Archive full notes in Client Database
    ├→ HubSpot: Log note on matched Deal/Contact
    ├→ Linear: Create tasks from action items
    └→ Gmail: Draft follow-up email to external attendees
```

Configure each step as a separate Zapier action in a single multi-step Zap, or use Zapier Paths for conditional routing (internal vs. external meetings).

## Output
- Native integrations connected and authorized
- Auto-post rules configured per folder/channel
- CRM sync tested with sample meeting data
- Multi-integration workflows validated end-to-end

## Error Handling

| Integration | Error | Fix |
|-------------|-------|-----|
| Slack | "Channel not found" | Channel may be renamed; verify name and invite Granola bot |
| Notion | "Cannot share" | Reconnect Notion; Granola's database may have been deleted |
| HubSpot | "No matching contact" | Create the contact in HubSpot first, then re-share |
| Attio | "Record not found" | Verify attendee email matches an Attio Person record |
| Zapier | "Trigger not firing" | Reconnect Granola in Zapier; check folder name matches exactly |
| All | "Authorization expired" | Disconnect and reconnect the integration in Settings |

## Resources
- [Integrations Overview](https://docs.granola.ai/help-center/sharing/integrations/integrations-with-granola)
- [HubSpot Integration Blog](https://www.granola.ai/blog/granola-hubspot-integration-crm-updates)
- [Notion Setup](https://docs.granola.ai/help-center/sharing/notion)
- [Slack Huddles Guide](https://www.granola.ai/blog/how-to-use-granola-slack-huddles)
- [Attio Integration](https://attio.com/apps/granola)
- [Zapier Granola App](https://zapier.com/apps/granola/integrations)

## Next Steps
Proceed to `granola-webhooks-events` for event-driven automation patterns.
