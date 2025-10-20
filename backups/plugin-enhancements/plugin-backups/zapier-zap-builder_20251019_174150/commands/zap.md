---
description: Build Zapier Zap configurations
---

# Zapier Zap Builder

Create multi-step Zapier automation configurations with filters, paths, and AI integration.

## Usage

When users request Zapier automations, design complete Zaps with step-by-step configuration.

## Zap Structure

Every Zap has:
1. **Trigger** - What starts the Zap
2. **Action Steps** - What the Zap does
3. **Filters** (optional) - Conditional logic
4. **Paths** (optional) - Branching logic
5. **Formatters** (optional) - Data transformation

## Common Zap Templates

### 1. AI Email Assistant
```
Trigger: Gmail - New Email
Filter: Subject contains "support"
Action 1: OpenAI - Send Prompt (draft response)
Action 2: Gmail - Send Email (with AI response)
Action 3: Google Sheets - Create Row (log)
```

### 2. Lead Capture & Qualification
```
Trigger: Webhook - Catch Hook (form submission)
Action 1: OpenAI - Send Prompt (score lead 0-100)
Filter: Score > 70
Action 2: Slack - Send Channel Message (alert sales)
Action 3: HubSpot - Create Contact & Deal
```

### 3. Content Distribution
```
Trigger: RSS by Zapier - New Item in Feed
Action 1: OpenAI - Send Prompt (rewrite for social)
Paths:
  Path A: Twitter - Create Tweet
  Path B: LinkedIn - Create Share Update
  Path C: Facebook - Create Page Post
```

### 4. Calendar to Task Automation
```
Trigger: Google Calendar - Event Start
Filter: Event contains "meeting"
Action 1: OpenAI - Send Prompt (extract action items)
Action 2: Todoist - Create Task
Action 3: Gmail - Send Email (summary to attendees)
```

### 5. Invoice Processing
```
Trigger: Gmail - New Attachment
Filter: Filename contains "invoice"
Action 1: Formatter - Extract Pattern (invoice number)
Action 2: OpenAI - Send Prompt (extract data)
Action 3: Google Sheets - Create Row
Action 4: Slack - Send Direct Message (notify accounting)
```

## Zapier Features

### Filters
Add conditional logic between steps:
```
Filter: Only continue if...
  - Field: {{email}}
  - Condition: Contains
  - Value: @company.com
```

### Paths
Create branching logic:
```
Paths: Branch your Zap
  Path A: High Priority
    - Filter: Priority is "high"
    - Action: Send to Slack #urgent
  Path B: Normal Priority
    - Filter: Priority is "normal"
    - Action: Add to task list
  Path C: Everything Else
    - Action: Archive
```

### Formatters
Transform data:
```
Formatter by Zapier
  - Transform: Text
  - Action: Capitalize
  - Input: {{name}}

Formatter by Zapier
  - Transform: Date/Time
  - Action: Format
  - Input: {{date}}
  - To Format: MM/DD/YYYY
```

### Delays
Add time delays:
```
Delay by Zapier
  - Type: For
  - Time: 1 hour
```

### AI Integration
Use OpenAI directly:
```
OpenAI - Send Prompt
  - Model: GPT-4
  - User Message: "Analyze this data: {{data}}"
  - Max Tokens: 500
  - Temperature: 0.7
```

## Zapier Plans & Pricing

| Plan | Price | Tasks | Multi-Step | Premium Apps |
|------|-------|-------|------------|--------------|
| Free | $0 | 100/mo |  |  |
| Starter | $20/mo | 750/mo |  |  |
| Professional | $49/mo | 2,000/mo |  |  |
| Team | $69/mo | 2,000/mo |  |  |

**Tasks:** Each action step counts as 1 task

## Design Pattern

When creating a Zap, provide:

```markdown
## Zap: [Name]

### Purpose
[What this automates]

### Steps

**Trigger: [App] - [Event]**
- Setting 1: Value
- Setting 2: Value

**Action 1: [App] - [Action]**
- Field 1: {{trigger.field}}
- Field 2: Value

**Filter: Only continue if...**
- Condition: Value

**Action 2: [App] - [Action]**
- Map data fields

### Testing
1. Test trigger with sample data
2. Verify each action executes
3. Check data mapping
4. Turn on Zap

### Cost Estimate
- Steps per run: X
- Expected monthly runs: Y
- Total tasks: Z
- Plan needed: [Starter/Professional]
```

## Best Practices

1. **Use filters to save tasks** - Filter early to avoid unnecessary actions
2. **Formatter before action** - Transform data before using it
3. **Test thoroughly** - Use Zapier's test feature for each step
4. **Error notifications** - Add email/Slack on Zap errors
5. **Name clearly** - Use descriptive Zap names
6. **Monitor usage** - Watch task consumption
7. **Use paths sparingly** - Each path multiplies tasks
8. **Leverage webhooks** - Faster than polling
9. **Batch when possible** - Some apps support bulk actions
10. **Document in description** - Add notes about the Zap purpose

## Common Integrations

### Most Popular
- Gmail, Google Sheets, Google Calendar
- Slack, Microsoft Teams
- HubSpot, Salesforce
- Airtable, Notion
- Stripe, PayPal
- Twitter, LinkedIn, Facebook

### AI Integrations
- OpenAI (GPT-4, DALL-E)
- Anthropic Claude (via webhooks)
- Google Gemini
- Cohere
- Custom AI APIs (via webhooks)

## Example: Complete Zap Configuration

```markdown
## Zap: AI-Powered Customer Support Automation

### Purpose
Automatically classify and respond to support emails using AI.

### Configuration

**Trigger: Gmail - New Email in Mailbox**
- Mailbox: support@company.com
- Label: INBOX

**Filter: Only continue if Email Subject doesn't contain "Re:"**

**Action 1: OpenAI - Send Prompt**
- Model: GPT-4
- System Message: "You are a helpful customer support assistant."
- User Message: "Classify this support email as urgent/normal/low priority and suggest a response:\n\nFrom: {{trigger.From}}\nSubject: {{trigger.Subject}}\nBody: {{trigger.Body Plain}}"
- Max Tokens: 500
- Temperature: 0.7

**Paths: Branch based on priority**

Path A: Urgent
- Filter: {{openai.choices[0].message.content}} contains "urgent"
- Action: Slack - Send Channel Message
  - Channel: #support-urgent
  - Message: " Urgent support email from {{trigger.From}}"

Path B: Normal/Low
- Action: Gmail - Create Draft
  - To: {{trigger.From}}
  - Subject: Re: {{trigger.Subject}}
  - Body: {{openai.choices[0].message.content}}

**Action (all paths): Google Sheets - Create Spreadsheet Row**
- Spreadsheet: Support Tickets
- From: {{trigger.From}}
- Subject: {{trigger.Subject}}
- Priority: [extracted from AI]
- Date: {{trigger.Date}}

### Testing Steps
1. Send test email to support@company.com
2. Verify trigger captures email
3. Check OpenAI classification
4. Confirm path routing works
5. Validate Slack notification (urgent path)
6. Check draft creation (normal path)
7. Verify Sheets logging

### Cost Estimate
- Trigger: 0 tasks
- Filter: 0 tasks
- OpenAI: 1 task
- Paths: Split into 2, but only 1 executes
- Path actions: 1-2 tasks depending on path
- Sheets: 1 task
**Total:** 3-4 tasks per email

At 100 emails/month: 300-400 tasks
**Plan needed:** Starter ($20/mo, includes 750 tasks)

### Setup Time
15-20 minutes

### Business Impact
- Response time: Reduced by 60%
- Support team: Focus on complex issues
- Customer satisfaction: +25%
```

## Troubleshooting

### "This Zap would exceed your task limit"
- Add filters to reduce executions
- Upgrade plan
- Split into multiple Zaps

### "We couldn't find a [field]"
- Check trigger test data
- Use correct field mapping
- Add formatter if needed

### "Zap is slow"
- Use webhooks instead of polling
- Reduce delay steps
- Optimize filters

### "Action failed"
- Check app permissions
- Verify API limits
- Review error details
- Add error handling

## When to Use Zapier

**Use Zapier when:**
- Need easiest setup (non-technical)
- Want largest app ecosystem (5000+)
- Prefer managed service
- Willing to pay for simplicity

**Use n8n when:**
- Need complex logic
- Want self-hosting
- Processing high volumes
- Want lower costs

**Use Make when:**
- Want visual design
- Need advanced data mapping
- Prefer middle ground on pricing

All three are excellent - choose based on your priorities!
