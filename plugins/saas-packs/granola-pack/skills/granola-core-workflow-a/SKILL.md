---
name: granola-core-workflow-a
description: |
  Meeting preparation and template setup in Granola — templates, recipes, and pre-meeting workflows.
  Use when configuring note templates for 1:1s, standups, discovery calls, or sprint planning,
  creating custom recipes, or preparing agenda notes before important meetings.
  Trigger: "granola template", "granola meeting prep", "granola recipe", "granola agenda".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, workflow, templates]

---
# Granola Core Workflow A: Meeting Preparation & Templates

## Overview
Configure Granola templates (which structure the enhanced output) and recipes (repeatable Chat prompts) for consistent, high-quality meeting notes. Granola ships with 29 built-in templates and supports custom templates per workspace.

## Prerequisites
- Granola installed and authenticated
- Calendar synced with upcoming meetings
- At least one meeting captured (to understand the enhancement flow)

## Instructions

### Step 1 — Choose a Built-in Template
Click the **Change template** icon at the bottom of your notes before or during a meeting:

| Template | Best For | Sections Generated |
|----------|----------|-------------------|
| **1-on-1** | Manager/report check-ins | Check-in, Updates, Discussion, Action Items |
| **Stand-up** | Daily sync | Progress, Blockers, Priorities |
| **Discovery Call** | Sales prospecting | Budget, Authority, Need, Timeline (BANT) |
| **Sprint Planning** | Agile ceremonies | Sprint Goals, Velocity, Backlog, Risks |
| **Weekly Team** | Status meetings | Updates, Decisions, Action Items |
| **Interview Debrief** | Hiring loops | Candidate Assessment, Strengths, Concerns |
| **Project Kick-Off** | New initiatives | Goals, Scope, Timeline, RACI |
| **Pipeline Review** | Sales forecast | Deal Status, Next Steps, Risks |
| **Design Crit** | Creative review | Feedback, Changes Requested, Approvals |

Templates tell the AI how to structure the enhanced output — a sales call produces different sections than a standup.

### Step 2 — Create a Custom Template
1. Open Granola Settings > **Templates**
2. Click **Create New Template**
3. Define the structure using section headers:

```markdown
## Customer Feedback Session

### Context
[Brief on the customer and their product usage]

### Key Feedback Themes
[Grouped by category: UX, Performance, Features, Support]

### Verbatim Quotes
[Direct customer quotes with timestamps]

### Severity Assessment
[Critical / High / Medium / Low for each issue]

### Action Items
[Owner, task, due date]

### Follow-Up Commitment
[What we promised the customer and by when]
```

4. Name it and optionally set auto-trigger conditions:
   - Calendar event title contains specific keywords (e.g., "feedback", "customer")
   - Attendee email domains (e.g., `@customer.com`)

### Step 3 — Create Recipes for Granola Chat
Recipes are saved prompts invoked with `/` in Granola Chat:

| Recipe | Prompt | Use Case |
|--------|--------|----------|
| `/follow-up` | "Draft a professional follow-up email summarizing decisions and next steps" | Post-meeting email |
| `/standup` | "Extract blockers, progress updates, and priorities per person" | Standup summary |
| `/bant` | "Analyze this call using BANT framework (Budget, Authority, Need, Timeline)" | Sales qualification |
| `/prd` | "Write a PRD based on the product requirements discussed in this meeting" | Product spec |
| `/coaching` | "Based on this 1:1, suggest coaching points and development areas" | Manager prep |
| `/decision-log` | "List all decisions made, who made them, and the reasoning" | Governance |

Create custom recipes at Settings > **Recipes** or directly in Chat.

### Step 4 — Pre-Meeting Preparation
Before important meetings, type context into the Granola notepad **before** the call starts:

```markdown
## Pre-Meeting Context
- Last meeting: discussed Series A timeline, concerns about runway
- Open items: term sheet review, board seat allocation
- My goals today: confirm valuation range, discuss liquidation preference
- Questions to ask: timeline for closing, co-investor status
```

When you click **Enhance Notes** after the meeting, Granola combines:
1. Your pre-meeting context
2. Your live notes during the meeting
3. The full audio transcript

This produces output that is aware of your goals and prior context.

### Step 5 — Set Template Defaults per Workspace
For team deployments, set default templates per shared folder:

| Folder | Default Template | Auto-Apply |
|--------|-----------------|------------|
| `#sales-calls` | Discovery Call | Events with external attendees |
| `#engineering` | Sprint Planning | Events titled "sprint" or "planning" |
| `#leadership` | Weekly Team | Events with >5 attendees |
| `#interviews` | Interview Debrief | Events titled "interview" |

## Output
- Templates configured for each meeting type
- Custom recipes created for post-meeting workflows
- Pre-meeting context workflow established
- Consistent structured output across team meetings

## Error Handling

| Issue | Cause | Fix |
|-------|-------|-----|
| Wrong template applied | Auto-trigger matched incorrectly | Narrow trigger conditions (more specific keywords) |
| Template sections empty | Meeting lacked relevant discussion | Remove irrelevant sections from template |
| Recipe not appearing | Not saved to workspace | Save recipe in Settings > Recipes |
| Pre-meeting notes lost | Typed in wrong app | Ensure you type in the Granola notepad, not a separate editor |

## Template Design Best Practices
1. **Use clear section headers** — Granola's AI parses headers to organize content
2. **Include bracketed hints** — `[Owner, task, due date]` guides the AI output format
3. **Keep templates under 10 sections** — too many sections dilute content
4. **Add a "Verbatim Quotes" section** for customer-facing meetings — captures exact language
5. **End with "Action Items" and "Next Steps"** — the AI reliably fills these

## Resources
- [Customize Notes with Templates](https://docs.granola.ai/help-center/taking-notes/customise-notes-with-templates)
- [Introducing Recipes](https://www.granola.ai/blog/say-hello-to-recipes)
- [Get the Best from Granola](https://www.granola.ai/blog/get-the-best-from-granola)

## Next Steps
Proceed to `granola-core-workflow-b` for post-meeting processing and sharing workflows.
