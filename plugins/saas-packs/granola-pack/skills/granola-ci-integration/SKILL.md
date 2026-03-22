---
name: granola-ci-integration
description: |
  Build automated pipelines from Granola meeting notes to GitHub Issues, Linear tasks,
  Slack notifications, and documentation updates using Zapier and GitHub Actions.
  Trigger: "granola CI", "granola automation pipeline", "granola to github",
  "granola to linear", "meeting notes automation".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, granola, ci-cd, automation]

---
# Granola CI Integration

## Overview
Build automated pipelines that process Granola meeting notes into development artifacts: GitHub Issues from action items, Linear tasks with team routing, Slack digests for stakeholders, and meeting logs in your repository. Uses Zapier as the middleware between Granola and dev tools.

## Prerequisites
- Granola Business plan (for Zapier access)
- Zapier account (Free for basic, Paid for multi-step Zaps)
- GitHub repository with Actions enabled
- Optional: Linear account, Slack workspace

## Instructions

### Step 1 — Set Up the Zapier Pipeline

```yaml
# Pipeline: Granola → Zapier → GitHub + Slack + Linear

Trigger:
  App: Granola
  Event: Note Added to Granola Folder
  Folder: "Engineering"  # Only process engineering meetings
```

### Step 2 — Parse Action Items with Zapier Code

Add a Code by Zapier step (JavaScript) to extract action items:

```javascript
// Zapier Code Step — Extract action items from Granola note
const noteContent = inputData.note_content || '';
const meetingTitle = inputData.title || 'Untitled Meeting';
const meetingDate = inputData.calendar_event_datetime || new Date().toISOString();

// Extract action items: matches "- [ ] @person: task" or "- [ ] task"
const actionRegex = /- \[ \] @?(\w+):?\s+(.+)/g;
const actions = [];
let match;

while ((match = actionRegex.exec(noteContent)) !== null) {
  actions.push({
    assignee: match[1],
    task: match[2].trim(),
    meeting: meetingTitle,
    date: meetingDate.split('T')[0],
  });
}

// Extract decisions: lines starting with "- " under "## Decisions" or "## Key Decisions"
const decisionSection = noteContent.match(/## (?:Key )?Decisions\n([\s\S]*?)(?=\n##|$)/);
const decisions = decisionSection
  ? decisionSection[1].split('\n').filter(l => l.startsWith('- ')).map(l => l.replace('- ', ''))
  : [];

output = [{
  action_count: actions.length,
  actions: JSON.stringify(actions),
  decisions: decisions.join('; '),
  meeting_title: meetingTitle,
  meeting_date: meetingDate,
}];
```

### Step 3 — Create GitHub Issues from Action Items

```yaml
# For each action item, create a GitHub issue
Action:
  App: GitHub
  Event: Create Issue
  Repository: "your-org/your-repo"
  Title: "Meeting Action: {{task}} [{{date}}]"
  Body: |
    ## Context
    From meeting: **{{meeting}}** on {{date}}

    ## Task
    {{task}}

    ## Assigned To
    @{{assignee}}

    ---
    *Auto-created from Granola meeting notes*
  Labels: "meeting-action"
  Assignee: "{{assignee}}"  # Must match GitHub username
```

### Step 4 — GitHub Actions Workflow for Meeting Logs

Create a workflow triggered by Zapier via `repository_dispatch`:

```yaml
# .github/workflows/meeting-log.yml
name: Update Meeting Log

on:
  repository_dispatch:
    types: [granola-meeting]

jobs:
  update-log:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Append to meeting log
        run: |
          MEETING_TITLE="${{ github.event.client_payload.title }}"
          MEETING_DATE="${{ github.event.client_payload.date }}"
          DECISIONS="${{ github.event.client_payload.decisions }}"
          ACTION_COUNT="${{ github.event.client_payload.action_count }}"

          mkdir -p docs/meetings

          cat >> docs/meetings/log.md << EOF

          ## ${MEETING_DATE} — ${MEETING_TITLE}
          - **Decisions:** ${DECISIONS}
          - **Action items created:** ${ACTION_COUNT}
          - **Source:** Granola AI
          EOF

      - name: Commit and push
        run: |
          git config user.name "Granola Bot"
          git config user.email "bot@granola.ai"
          git add docs/meetings/log.md
          git commit -m "docs: meeting log — ${MEETING_DATE}" || echo "No changes"
          git push
```

Trigger from Zapier using the Webhooks action:
```yaml
Action:
  App: Webhooks by Zapier
  Event: POST
  URL: https://api.github.com/repos/your-org/your-repo/dispatches
  Headers:
    Authorization: "Bearer {{github_pat}}"
    Accept: "application/vnd.github.v3+json"
  Body:
    event_type: "granola-meeting"
    client_payload:
      title: "{{meeting_title}}"
      date: "{{meeting_date}}"
      decisions: "{{decisions}}"
      action_count: "{{action_count}}"
```

### Step 5 — Linear Task Creation

```yaml
Action:
  App: Linear
  Event: Create Issue
  Team: Engineering
  Title: "{{task}}"
  Description: "From meeting: {{meeting}} ({{date}})\n\nAssigned: @{{assignee}}"
  Label: "meeting-action"
  Priority: "Medium"
```

### Step 6 — Slack Notification

```yaml
Action:
  App: Slack
  Event: Send Channel Message
  Channel: "#engineering-meetings"
  Message: |
    :memo: *Meeting Notes Ready:* {{meeting_title}}
    :calendar: {{meeting_date}}

    *Decisions:*
    {{decisions}}

    *Action Items Created:* {{action_count}}
    :point_right: Check Linear/GitHub for assigned tasks

    [View full notes in Granola]
```

## Complete Pipeline Flow
```
Meeting ends → Granola enhances notes
  → Note added to "Engineering" folder
  → Zapier triggers
    ├→ Parse action items (Code step)
    ├→ Create GitHub Issues (per action item)
    ├→ Trigger GitHub Actions (update meeting log)
    ├→ Create Linear tasks (per action item)
    └→ Post Slack summary (#engineering-meetings)
```

## Output
- Action items automatically created as GitHub Issues and Linear tasks
- Meeting log updated in repository via GitHub Actions
- Slack summary posted to team channel
- Full audit trail from meeting to task completion

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Zapier trigger not firing | Note not in the configured folder | Verify folder name matches exactly |
| GitHub issue creation fails | PAT expired or insufficient scope | Regenerate PAT with `repo` scope |
| Action items not parsed | Note format doesn't match regex | Adjust regex for your template's action item format |
| Linear API error | Team name mismatch | Use Linear team ID instead of name |
| Slack message empty | Note still processing | Add 2-minute delay as first Zap step |

## Testing Checklist
- [ ] Schedule a test meeting with explicit action items
- [ ] Verify note lands in the correct Granola folder
- [ ] Confirm Zapier trigger fires (check Zap history)
- [ ] Verify GitHub issues created with correct labels and assignees
- [ ] Confirm meeting log committed to repository
- [ ] Check Slack message formatting in target channel
- [ ] Verify Linear tasks appear in correct team

## Resources
- [Zapier Granola App](https://zapier.com/apps/granola/integrations)
- [GitHub Actions: repository_dispatch](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#repository_dispatch)
- [Linear Zapier Integration](https://zapier.com/apps/linear/integrations)

## Next Steps
Proceed to `granola-deploy-integration` for native app integration setup.
