---
name: lindy-hello-world
description: |
  Create your first Lindy AI agent with a real trigger and action.
  Use when starting with Lindy, testing your setup,
  or learning basic agent workflow patterns.
  Trigger with phrases like "lindy hello world", "lindy example",
  "lindy quick start", "simple lindy agent", "first lindy".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, api, testing]

---
# Lindy Hello World

## Overview
Build a minimal Lindy AI agent: **Webhook Received** trigger -> LLM processing ->
**Slack notification**. Demonstrates the three core building blocks every Lindy agent
uses: Trigger, Agent Step (prompt + model + skills), and Action.

## Prerequisites
- Lindy account at https://app.lindy.ai
- Slack workspace connected (or Gmail for email variant)
- Completed `lindy-install-auth` setup

## Instructions

### Step 1: Create Agent via Dashboard
1. Click **"New Agent"** at https://app.lindy.ai
2. In the prompt field ("How can I help you?"), type:
   ```
   When I send a webhook, summarize the message and post it to Slack
   ```
3. Agent Builder auto-generates the workflow with trigger + action nodes

### Step 2: Configure the Webhook Trigger
1. Click the trigger node at the top of the workflow canvas
2. Select **Webhook Received**
3. Copy the generated URL:
   ```
   https://public.lindy.ai/api/v1/webhooks/<unique-id>
   ```
4. Click **Generate Secret** — copy immediately (shown once)

### Step 3: Add the Slack Action
1. Click **"+"** to add a step
2. Search for **Slack Send Channel Message**
3. Authorize your Slack workspace when prompted
4. Configure fields:
   - **Channel**: `#general` (or test channel)
   - **Message** field mode: **AI Prompt**
   - Instruction:
     ```
     Summarize the webhook payload in one sentence.
     Payload: {{webhook_received.request.body}}
     ```

### Step 4: Set the Agent Prompt
Open **Settings > Prompt**:
```
You are a webhook summarizer. When you receive a webhook payload,
extract the key information and create a concise one-sentence summary.
Be factual and specific. Do not add opinions or speculation.
```

### Step 5: Test It
```bash
curl -X POST "https://public.lindy.ai/api/v1/webhooks/YOUR_ID" \
  -H "Authorization: Bearer YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "order.created",
    "customer": "Jane Doe",
    "amount": 149.99,
    "items": ["Widget Pro", "Adapter Cable"]
  }'
```

Expected Slack message:
> Jane Doe placed a $149.99 order for Widget Pro and Adapter Cable.

### Step 6: Verify in Dashboard
Navigate to the **Tasks** tab in your agent view. Confirm status shows **Completed**.
Click into the task to see each step's input/output for debugging.

## Agent Anatomy

| Component | Purpose | Hello World Value |
|-----------|---------|-------------------|
| **Prompt** | Core behavioral instructions | "Summarize webhook payloads" |
| **Model** | AI engine powering decisions | Default (GPT-4 / Claude / Gemini) |
| **Skills** | Available actions & tools | Slack Send Channel Message |
| **Exit Conditions** | When the task is "done" | Message sent successfully |

## Webhook Data Variables

| Variable | Contents |
|----------|----------|
| `{{webhook_received.request.body}}` | Full JSON payload |
| `{{webhook_received.request.headers}}` | HTTP request headers |
| `{{webhook_received.request.query}}` | URL query parameters |

## Field Configuration Modes

| Mode | Behavior | Credit Cost |
|------|----------|-------------|
| **Auto** | Agent determines value from context | Standard |
| **AI Prompt** | Natural language instructions generate content | Standard |
| **Set Manually** | Exact value, no AI processing | Lower |

## Variant: Email Instead of Slack
Replace the Slack action with **Gmail Send Email**:
- **To**: Set manually or reference a webhook field
- **Subject**: AI Prompt — `"Summary: {{webhook_received.request.body.event}}"`
- **Body**: AI Prompt — `"Summarize this event: {{webhook_received.request.body}}"`

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook returns 401 | Missing Authorization header | Add `Bearer <secret>` header |
| Slack message not sent | Channel not authorized | Re-authorize Slack in Lindy |
| Task shows "Failed" | Action misconfigured | Check field references in step config |
| No task created | Agent not active | Publish/activate the agent |
| Empty summary | Payload not reaching LLM | Verify `{{webhook_received.request.body}}` reference |

## Cost
~1-3 credits per invocation on basic models. Free tier (400 credits/month) supports
~130-400 test runs per month.

## Resources
- [Getting Started 101](https://www.lindy.ai/academy-lessons/getting-started-101)
- [Webhook Triggers Academy](https://www.lindy.ai/academy-lessons/webhook-triggers)
- [Lindy Documentation](https://docs.lindy.ai)

## Next Steps
Proceed to `lindy-core-workflow-a` for a full multi-step agent workflow.
