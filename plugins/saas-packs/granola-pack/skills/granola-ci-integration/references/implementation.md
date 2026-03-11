# Granola CI Integration - Implementation Details

## Zapier Webhook Setup

### Parse Meeting Content
```javascript
// Zapier Code Step - Parse Action Items
const noteContent = inputData.note_content;
const actionPattern = /- \[ \] (.+?)(?:\(@(\w+)\))?/g;
const actions = [];
let match;
while ((match = actionPattern.exec(noteContent)) !== null) {
  actions.push({ task: match[1].trim(), assignee: match[2] || 'unassigned' });
}
return { actions: JSON.stringify(actions) };
```

### Create GitHub Issues from Actions
```yaml
Action: GitHub - Create Issue
Repository: your-org/your-repo
Title: "Meeting Action: {{task}}"
Body: |
  From meeting: {{meeting_title}}
  Date: {{meeting_date}}
  Task: {{task}}
  Assignee: {{assignee}}
  ---
  Auto-created by Granola integration
Labels: ["from-meeting", "action-item"]
```

## GitHub Actions Workflow

```yaml
# .github/workflows/process-meeting-notes.yml
name: Process Meeting Notes
on:
  repository_dispatch:
    types: [granola-meeting-completed]
jobs:
  process-notes:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Update Meeting Log
        run: |
          echo "| ${{ github.event.client_payload.date }} | ${{ github.event.client_payload.title }} | [Link](${{ github.event.client_payload.url }}) |" >> docs/meetings.md
      - name: Create Issues for Actions
        uses: actions/github-script@v7
        with:
          script: |
            const actions = JSON.parse('${{ github.event.client_payload.action_items }}');
            for (const action of actions) {
              await github.rest.issues.create({
                owner: context.repo.owner, repo: context.repo.repo,
                title: `Meeting Action: ${action.task}`,
                body: `From: ${{ github.event.client_payload.title }}\n\n${action.task}`,
                labels: ['meeting-action']
              });
            }
      - name: Commit Changes
        run: |
          git config user.name "Granola Bot"
          git config user.email "bot@granola.ai"
          git add docs/meetings.md
          git commit -m "docs: add meeting notes from ${{ github.event.client_payload.date }}"
          git push
```

### Trigger from Zapier
```yaml
Method: POST
URL: https://api.github.com/repos/your-org/your-repo/dispatches
Headers:
  Authorization: Bearer {{github_token}}
Body: {
  "event_type": "granola-meeting-completed",
  "client_payload": {
    "title": "{{meeting_title}}", "date": "{{meeting_date}}",
    "url": "{{granola_link}}", "action_items": {{action_items_json}}
  }
}
```

## Linear Integration Pipeline
```yaml
Step 1 - Trigger: Granola New Note Created
Step 2 - Filter: Summary contains "TODO" or "action item"
Step 3 - Parse: Code by Zapier - Extract action items
Step 4 - Loop: For each action item -> Linear Create Issue (Team: Engineering, State: Todo)
```

## Slack Meeting Summary Bot
```yaml
Trigger: New Granola Note
Channel: "#dev-meetings"
Blocks:
  - header: "Meeting Notes: {{meeting_title}}"
  - section: "{{summary}}"
  - divider
  - section: "*Action Items:*\n{{action_items}}"
  - actions:
    - button: "View Full Notes" (url: {{granola_link}})
    - button: "Create Tasks"
```

## Testing

```bash
# Test Zapier webhook with sample data
curl -X POST https://hooks.zapier.com/hooks/catch/YOUR_HOOK_ID \
  -H "Content-Type: application/json" \
  -d '{"meeting_title": "Test Sprint Planning", "meeting_date": "2025-01-06", "summary": "Discussed Q1 priorities", "action_items": [{"task": "Review PRs", "assignee": "mike"}]}'
```

## Error Handling
```yaml
On Error:
  Retry: 3 times
  Delay: 5 minutes between retries
  Fallback: Send error to Slack #ops-alerts
```
