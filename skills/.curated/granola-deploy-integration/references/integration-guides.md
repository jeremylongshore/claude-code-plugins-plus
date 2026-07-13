# Granola Integration Guides

## Slack Integration

### Setup

1. Navigate to Granola Settings > Integrations > Slack
2. Click "Connect Slack"
3. Select workspace and authorize permissions (post messages, access channels, read user info)
4. Configure default channel

### Configuration Options

| Setting | Options | Recommendation |
|---------|---------|----------------|
| Default channel | Any channel | #meeting-notes |
| Auto-post | On/Off | On for team meetings |
| Include summary | Yes/No | Yes |
| Include actions | Yes/No | Yes |
| Mention attendees | Yes/No | For important meetings |

### Message Format

```
Meeting Notes: Sprint Planning
January 6, 2025 | 45 minutes | 5 attendees

Summary:
Discussed Q1 priorities. Agreed on feature freeze
date of Jan 15th. Will focus on bug fixes next sprint.

Action Items:
- @sarah: Schedule design review (due: Jan 8)
- @mike: Create deployment checklist (due: Jan 10)
- @team: Review OKRs by Friday

[View Full Notes in Granola]
```

## Notion Integration

### Setup

1. Navigate to Granola Settings > Integrations > Notion
2. Click "Connect Notion" and select workspace
3. Grant permissions: insert content, read pages, update pages
4. Select target database

### Database Schema

```
Meeting Notes Database
├── Title (title)
├── Date (date)
├── Duration (number)
├── Attendees (multi-select)
├── Summary (rich text)
├── Action Items (relation → Tasks)
├── Tags (multi-select)
├── Status (select)
└── Granola Link (url)
```

### Page Template

```markdown
# {{meeting_title}}

**Date:** {{date}}
**Duration:** {{duration}} minutes
**Attendees:** {{attendees}}

---

## Summary
{{summary}}

## Key Discussion Points
{{key_points}}

## Decisions Made
{{decisions}}

## Action Items
{{action_items}}

---
*Captured with Granola*
```

## HubSpot Integration

### Setup

1. Navigate to Granola Settings > Integrations > HubSpot
2. Authorize with HubSpot account
3. Grant permissions: read/write contacts, notes, and deals
4. Configure contact matching

### Contact Matching Rules

| Attendee Email | Action |
|----------------|--------|
| Exists in HubSpot | Attach note to contact |
| New email | Create contact (optional) |
| Internal domain | Skip CRM entry |

## Zapier Integration Recipes

### Granola to Google Docs

```yaml
Trigger: New Granola Note
Action: Create Google Doc
Configuration:
  Folder: Team Meeting Notes
  Title: "{{meeting_title}} - {{date}}"
```

### Granola to Asana

```yaml
Trigger: New Granola Note
Filter: Contains action items
Action: Create Asana Task
Configuration:
  Project: Meeting Actions
  Assignee: Dynamic from parsed @mention
  Due Date: Parsed from note content
```

### Granola to Airtable

```yaml
Trigger: New Granola Note
Action: Create Airtable Record
Configuration:
  Base: Meeting Archive
  Table: Notes
  Fields: Title, Date, Summary, Action Count, Status, Link
```

## Multi-Integration Workflows

### Complete Meeting Follow-up

```yaml
1. Meeting ends in Granola
     ↓
2. Summary posted to Slack #team-channel
     ↓
3. Full notes created in Notion
     ↓
4. Action items created in Linear
     ↓
5. HubSpot contact updated (if external)
     ↓
6. Follow-up email drafted in Gmail
```

### Path-Based Routing

```yaml
Zapier Paths:
  Path A (Internal Meeting):
    → Slack notification → Notion page → Linear tasks

  Path B (Client Meeting):
    → Slack notification → Notion page → HubSpot note → Gmail draft

Filter: If attendees contain external domain → Path B, else → Path A
```

## Deployment Checklist

### Per-Integration

- [ ] Test with sample meeting first
- [ ] Verify data mapping correct
- [ ] Confirm permissions adequate
- [ ] Set up error notifications
- [ ] Document for team
- [ ] Monitor first week

### Full Suite Rollout

- Phase 1 (Week 1): Slack connected and tested, team notified
- Phase 2 (Week 2): Notion connected, database template finalized
- Phase 3 (Week 3): CRM and task management connected, full automation verified
