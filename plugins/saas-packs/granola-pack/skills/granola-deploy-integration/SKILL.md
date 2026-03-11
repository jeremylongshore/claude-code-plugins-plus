---
name: granola-deploy-integration
description: |
  Deploy Granola integrations to Slack, Notion, HubSpot, and other apps.
  Use when connecting Granola to productivity tools,
  setting up native integrations, or configuring auto-sync.
  Trigger with phrases like "granola slack", "granola notion",
  "granola hubspot", "granola integration", "connect granola".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Deploy Integration

## Overview
Configure and deploy native Granola integrations with Slack, Notion, HubSpot, and other productivity tools.

## Prerequisites
- Granola Pro or Business plan
- Admin access to target apps
- Integration requirements defined

## Native Integrations

### Slack Integration

#### Setup
```markdown
## Connect Slack

1. Granola Settings > Integrations > Slack
2. Click "Connect Slack"
3. Select workspace
4. Authorize permissions:
   - Post messages
   - Access channels
   - Read user info
5. Configure default channel
```

#### Configuration Options
| Setting | Options | Recommendation |
|---------|---------|----------------|
| Default channel | Any channel | #meeting-notes |
| Auto-post | On/Off | On for team meetings |
| Include summary | Yes/No | Yes |
| Include actions | Yes/No | Yes |
| Mention attendees | Yes/No | For important meetings |

#### Message Format
```
Meeting Notes: Sprint Planning
January 6, 2025 | 45 minutes | 5 attendees  # 2025 year

Summary:
Discussed Q1 priorities. Agreed on feature freeze
date of Jan 15th. Will focus on bug fixes next sprint.

Action Items:
- @sarah: Schedule design review (due: Jan 8)
- @mike: Create deployment checklist (due: Jan 10)
- @team: Review OKRs by Friday

[View Full Notes in Granola]
```

### Notion Integration

#### Setup
```markdown
## Connect Notion

1. Granola Settings > Integrations > Notion
2. Click "Connect Notion"
3. Select workspace
4. Choose integration permissions:
   - Insert content
   - Read pages
   - Update pages
5. Select target database
```

#### Database Schema
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

#### Page Template
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

### HubSpot Integration

#### Setup
```markdown
## Connect HubSpot

1. Granola Settings > Integrations > HubSpot
2. Click "Connect HubSpot"
3. Authorize with HubSpot account
4. Select permissions:
   - Read/Write contacts
   - Read/Write notes
   - Read/Write deals
5. Configure contact matching
```

#### Contact Matching Rules
| Attendee Email | Action |
|----------------|--------|
| Exists in HubSpot | Attach note to contact |
| New email | Create contact (optional) |
| Internal domain | Skip CRM entry |

#### Note Format
```
Meeting with {{contact_name}}
Date: {{date}}
Duration: {{duration}}

Summary: {{summary}}

Next Steps:
{{action_items}}

---
Captured with Granola
```

## Zapier Integrations

### Popular Zapier Recipes

#### Granola → Google Docs
```yaml
Trigger: New Granola Note
Action: Create Google Doc

Configuration:
  Folder: Team Meeting Notes
  Title: "{{meeting_title}} - {{date}}"
  Content: |
    # {{meeting_title}}

    **Date:** {{date}}
    **Attendees:** {{attendees}}

    ## Summary
    {{summary}}

    ## Action Items
    {{action_items}}
```

#### Granola → Asana
```yaml
Trigger: New Granola Note
Filter: Contains action items
Action: Create Asana Task

Configuration:
  Project: Meeting Actions
  Name: "Action from {{meeting_title}}"
  Notes: "{{action_text}}\n\nFrom meeting: {{meeting_title}}"
  Assignee: Dynamic from parsed @mention
  Due Date: Parsed from note content
```

#### Granola → Airtable
```yaml
Trigger: New Granola Note
Action: Create Airtable Record

Configuration:
  Base: Meeting Archive
  Table: Notes
  Fields:
    Title: {{meeting_title}}
    Date: {{date}}
    Summary: {{summary}}
    Action Count: {{action_item_count}}
    Status: Active
    Link: {{granola_url}}
```

## Multi-Integration Workflows

### Complete Meeting Follow-up
```yaml
# Multi-step automation

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

### Implementation
```yaml
Zapier Paths:
  Path A (Internal Meeting):
    → Slack notification
    → Notion page
    → Linear tasks

  Path B (Client Meeting):
    → Slack notification
    → Notion page
    → HubSpot note
    → Gmail draft

Filter:
  If attendees contain external domain → Path B
  Else → Path A
```

## Deployment Checklist

### Per-Integration
```markdown
## Integration Deployment

- [ ] Test with sample meeting first
- [ ] Verify data mapping correct
- [ ] Confirm permissions adequate
- [ ] Set up error notifications
- [ ] Document for team
- [ ] Monitor first week
```

### Full Suite
```markdown
## Complete Integration Rollout

Phase 1 (Week 1):
- [ ] Slack connected and tested
- [ ] Team notified of new workflow

Phase 2 (Week 2):
- [ ] Notion connected
- [ ] Database template finalized
- [ ] Historical import complete

Phase 3 (Week 3):
- [ ] CRM integration (if applicable)
- [ ] Task management connected
- [ ] Full automation verified
```

## Error Handling

| Integration | Common Error | Solution |
|-------------|--------------|----------|
| Slack | Channel not found | Verify channel exists |
| Notion | Database missing | Recreate target database |
| HubSpot | Contact mismatch | Update matching rules |
| Zapier | Rate limited | Add delays to Zap |

## Resources
- [Granola Integrations](https://granola.ai/integrations)
- [Zapier Granola App](https://zapier.com/apps/granola)
- [Integration FAQ](https://granola.ai/help/integrations)

## Next Steps
Proceed to `granola-webhooks-events` for event-driven automation.

## Instructions

1. Assess the current state of the deployment configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

## Examples

**Basic usage**: Apply granola deploy integration to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola deploy integration for production environments with multiple constraints and team-specific requirements.