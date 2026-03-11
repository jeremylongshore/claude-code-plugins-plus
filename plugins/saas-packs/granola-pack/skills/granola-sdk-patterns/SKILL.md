---
name: granola-sdk-patterns
description: |
  Zapier integration patterns and automation workflows for Granola.
  Use when building automated workflows, connecting Granola to other apps,
  or creating custom integrations via Zapier.
  Trigger with phrases like "granola zapier", "granola automation",
  "granola integration patterns", "granola SDK", "granola API".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Granola SDK Patterns

## Overview
Build powerful automations using Granola's Zapier integration to connect with 8,000+ apps.

## Prerequisites
- Granola Pro or Business plan
- Zapier account (Free tier works for basic automations)
- Target integration apps configured

## Available Triggers

### Granola Zapier Triggers
| Trigger | Description | Use Case |
|---------|-------------|----------|
| New Note Created | Fires when meeting ends | Sync to docs |
| Note Updated | Fires on note edits | Update CRM |
| Action Item Added | Fires for new todos | Create tickets |

## Common Integration Patterns

### Pattern 1: Notes to Notion
```yaml
Trigger: New Granola Note
Action: Create Notion Page

Configuration:
  Notion Database: Meeting Notes
  Title: {{meeting_title}}
  Date: {{meeting_date}}
  Content: {{note_content}}
  Participants: {{attendees}}
```

### Pattern 2: Action Items to Linear
```yaml
Trigger: New Granola Note
Filter: Contains "Action Item" or "TODO"
Action: Create Linear Issue

Configuration:
  Team: Engineering
  Title: "Meeting Action: {{action_text}}"
  Description: "From meeting: {{meeting_title}}"
  Assignee: {{extracted_assignee}}
```

### Pattern 3: Summary to Slack
```yaml
Trigger: New Granola Note
Action: Post to Slack Channel

Configuration:
  Channel: #team-updates
  Message: |
    :notepad_spiral: Meeting Notes: {{meeting_title}}

    **Summary:** {{summary}}

    **Action Items:**
    {{action_items}}

    Full notes: {{granola_link}}
```

### Pattern 4: CRM Update (HubSpot)
```yaml
Trigger: New Granola Note
Filter: Meeting contains client name
Action: Update HubSpot Contact

Configuration:
  Contact: {{client_email}}
  Note: "Meeting on {{date}}: {{summary}}"
  Last Contact: {{meeting_date}}
```

## Multi-Step Workflow Example

```yaml
Name: Complete Meeting Follow-up

Step 1 - Trigger:
  App: Granola
  Event: New Note Created

Step 2 - Action:
  App: OpenAI
  Event: Generate Follow-up Email
  Prompt: "Write a follow-up email for: {{summary}}"

Step 3 - Action:
  App: Gmail
  Event: Create Draft
  To: {{attendees}}
  Subject: "Follow-up: {{meeting_title}}"
  Body: {{openai_response}}

Step 4 - Action:
  App: Notion
  Event: Create Page
  Content: {{full_notes}}

Step 5 - Action:
  App: Slack
  Event: Send Message
  Message: "Follow-up draft ready for {{meeting_title}}"
```

## Output
- Zapier workflow configured
- Notes automatically synced to target apps
- Action items converted to tickets
- Follow-up communications automated

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Trigger Not Firing | Zapier connection expired | Reconnect Granola in Zapier |
| Missing Data | Note still processing | Add 2-min delay step |
| Rate Limited | Too many requests | Reduce Zap frequency |
| Format Errors | Data structure mismatch | Use Zapier Formatter |

## Best Practices
1. **Add delays** - Wait 2 min after meeting for processing
2. **Use filters** - Only trigger for relevant meetings
3. **Test first** - Use Zapier's test feature
4. **Monitor usage** - Check Zapier task limits

## Resources
- [Granola Zapier App](https://zapier.com/apps/granola)
- [Zapier Multi-Step Zaps](https://zapier.com/help/create/multi-step-zaps)
- [Granola Integration Docs](https://granola.ai/integrations)

## Next Steps
Proceed to `granola-core-workflow-a` for meeting preparation workflows.

## Instructions

1. Assess the current state of the API configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference

## Examples

**Basic usage**: Apply granola sdk patterns to a standard project setup with default configuration options.

**Advanced scenario**: Customize granola sdk patterns for production environments with multiple constraints and team-specific requirements.