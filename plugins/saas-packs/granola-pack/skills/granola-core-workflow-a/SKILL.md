---
name: granola-core-workflow-a
description: |
  Meeting preparation and template setup workflow with Granola.
  Use when preparing for important meetings, setting up note templates,
  or configuring meeting-specific capture settings.
  Trigger with phrases like "granola meeting prep", "granola template",
  "prepare granola meeting", "granola agenda", "granola setup meeting".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola Core Workflow A: Meeting Preparation

## Overview
Prepare for meetings with custom templates and pre-configured capture settings in Granola.

## Prerequisites
- Granola installed and authenticated
- Calendar synced with upcoming meetings
- Understanding of meeting types you commonly run

## Instructions

### Step 1: Create Meeting Templates

#### 1:1 Template
```markdown
# 1:1 Meeting Template

## Check-in
- How are you doing?
- Any blockers?

## Updates
- [ ] Progress on current goals
- [ ] Upcoming priorities

## Discussion Topics
-

## Action Items
- [ ]

## Next Meeting Focus
-
```

#### Sprint Planning Template
```markdown
# Sprint Planning Template

## Sprint Goals
-

## Velocity Review
- Last sprint: X points
- Capacity this sprint: Y points

## Backlog Items
| Story | Points | Assignee |
|-------|--------|----------|
|       |        |          |

## Risks & Dependencies
-

## Action Items
- [ ]
```

#### Client Meeting Template
```markdown
# Client Meeting Template

## Attendees
- Client:
- Internal:

## Agenda
1.
2.
3.

## Discussion Notes


## Decisions Made
-

## Action Items
| Item | Owner | Due Date |
|------|-------|----------|
|      |       |          |

## Next Steps
-
```

### Step 2: Configure in Granola
1. Open Granola app
2. Go to Settings > Templates
3. Click "Create New Template"
4. Paste your template content
5. Name it (e.g., "1:1 Meeting")
6. Set trigger conditions (optional):
   - Calendar event title contains "1:1"
   - Specific attendee domains

### Step 3: Pre-Meeting Checklist
Before important meetings:

```markdown
## Pre-Meeting Checklist

### 30 Minutes Before
- [ ] Review previous meeting notes
- [ ] Prepare agenda items
- [ ] Check Granola is running
- [ ] Test audio input

### 5 Minutes Before
- [ ] Open relevant documents
- [ ] Have action items from last meeting ready
- [ ] Open Granola notepad
- [ ] Add agenda to notes pane
```

### Step 4: Set Up Smart Defaults
Configure Granola preferences for automatic behavior:

| Setting | Recommended Value | Purpose |
|---------|------------------|---------|
| Auto-start recording | On | Never miss a meeting |
| Default template | By meeting type | Consistent structure |
| Auto-share | Team members | Immediate collaboration |
| Summary style | Detailed | Comprehensive notes |

## Output
- Custom templates for each meeting type
- Pre-meeting preparation workflow
- Consistent meeting structure
- Improved meeting outcomes

## Template Best Practices
1. **Keep templates focused** - One template per meeting type
2. **Include prompts** - Guide note-taking during meeting
3. **Pre-fill context** - Add relevant background
4. **Structure for AI** - Use headers for better parsing

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Template not loading | Wrong trigger condition | Check template settings |
| Missing sections | Template incomplete | Review and add sections |
| Conflicting templates | Multiple matches | Make triggers more specific |

## Resources
- [Granola Templates Gallery](https://granola.ai/templates)
- [Meeting Preparation Tips](https://granola.ai/blog/meeting-prep)

## Next Steps
Proceed to `granola-core-workflow-b` for post-meeting processing workflows.

## Examples

**Basic usage**: Apply granola core workflow a to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola core workflow a for production environments with multiple constraints and team-specific requirements.