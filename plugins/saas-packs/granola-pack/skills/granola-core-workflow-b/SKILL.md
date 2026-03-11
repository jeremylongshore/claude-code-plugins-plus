---
name: granola-core-workflow-b
description: |
  Post-meeting note processing and sharing workflow with Granola.
  Use when reviewing meeting notes, sharing with team members,
  or processing action items after meetings.
  Trigger with phrases like "granola post meeting", "share granola notes",
  "granola follow up", "process meeting notes", "granola action items".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Core Workflow B: Post-Meeting Processing

## Overview
Process, enhance, and share Granola meeting notes for maximum team productivity.

## Prerequisites
- Completed meeting with Granola capture
- Notes generated (typically 1-2 minutes after meeting)
- Team sharing preferences configured

## Instructions

### Step 1: Review AI-Generated Notes
Immediately after meeting ends:

1. Open Granola
2. Find meeting in recent list
3. Review generated content:
   - Summary accuracy
   - Action items captured
   - Key points highlighted
   - Participant attribution

### Step 2: Enhance Notes
Edit and improve AI output:

```markdown
## Review Checklist
- [ ] Correct any transcription errors
- [ ] Add context AI might have missed
- [ ] Clarify ambiguous action items
- [ ] Add links to referenced documents
- [ ] Tag relevant team members
- [ ] Mark confidential sections
```

### Step 3: Extract and Assign Action Items
Process action items for tracking:

```markdown
## Action Item Processing

### From Meeting: Sprint Planning 2025-01-06

| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| Update API documentation | @mike | Jan 8 | Pending |
| Review design mockups | @sarah | Jan 7 | Pending |
| Schedule client demo | @alex | Jan 10 | Pending |

### Export Format (for ticket systems):
- [ ] [HIGH] Update API documentation (@mike, due: 2025-01-08)
- [ ] [MED] Review design mockups (@sarah, due: 2025-01-07)
- [ ] [MED] Schedule client demo (@alex, due: 2025-01-10)
```

### Step 4: Share with Stakeholders

#### Share via Granola
1. Click "Share" button
2. Select recipients or copy link
3. Set permissions (view/edit)
4. Send with optional message

#### Share via Integrations
```yaml
Slack:
  Channel: #team-meeting-notes
  Format: Summary + Action Items

Notion:
  Database: Meeting Archive
  Page: Full notes with transcript

Email:
  Recipients: Meeting attendees
  Content: Summary + Action Items
  Attachment: PDF export
```

### Step 5: Archive and Categorize
Organize for future reference:

```markdown
## Filing System

Folder Structure:
/meetings
  /2025  # 2025 year
    /q1
      /project-alpha
        2025-01-06-sprint-planning.md
        2025-01-08-client-sync.md
      /team-1-1s
        2025-01-06-sarah-1-1.md

Tags:
- #decision - Contains key decisions
- #action-items - Has pending tasks
- #client - External stakeholder present
- #confidential - Sensitive content
```

## Post-Meeting Checklist
```markdown
## Within 5 Minutes
- [ ] Review AI summary for accuracy
- [ ] Correct obvious transcription errors
- [ ] Confirm action items are captured

## Within 1 Hour
- [ ] Share notes with attendees
- [ ] Create tickets for action items
- [ ] Send follow-up email if needed

## Within 24 Hours
- [ ] Archive in project folder
- [ ] Update relevant documentation
- [ ] Schedule follow-up meetings if needed
```

## Output
- Reviewed and enhanced meeting notes
- Action items extracted and assigned
- Notes shared with stakeholders
- Meeting properly archived

## Sharing Best Practices
1. **Share promptly** - Within 1 hour while fresh
2. **Highlight decisions** - Make outcomes clear
3. **Assign owners** - Every action needs an owner
4. **Set due dates** - Create accountability
5. **Link to source** - Reference full notes

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Notes not appearing | Still processing | Wait 2-5 minutes |
| Sharing failed | Permission issue | Check recipient access |
| Action items missing | Not stated clearly | Add manually |
| Wrong attendees | Calendar mismatch | Edit attendee list |

## Resources
- [Granola Sharing Options](https://granola.ai/help/sharing)
- [Follow-up Best Practices](https://granola.ai/blog/follow-up)

## Next Steps
Proceed to `granola-common-errors` for troubleshooting common issues.

## Examples

**Basic usage**: Apply granola core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola core workflow b for production environments with multiple constraints and team-specific requirements.