---
name: lindy-core-workflow-a
description: |
  Build and configure multi-step Lindy AI agent workflows.
  Use when creating agents with triggers, actions, conditions,
  knowledge bases, or agent steps.
  Trigger with phrases like "create lindy agent", "build lindy agent",
  "lindy agent workflow", "configure lindy agent", "lindy workflow".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, workflow]

---
# Lindy Core Workflow A: Agent Creation

## Overview
Complete workflow for creating, configuring, and testing Lindy AI agents.
Agents consist of four components: **Prompt** (behavioral instructions),
**Model** (AI engine), **Skills** (available actions), and **Exit Conditions**
(completion criteria).

## Prerequisites
- Lindy account at https://app.lindy.ai
- Use case defined (support bot, email triage, data processor, etc.)
- Required integrations identified (Slack, Gmail, Sheets, etc.)

## Instructions

### Step 1: Define Agent Specification
Before building, document:
- **Purpose**: What the agent does (one sentence)
- **Trigger**: What wakes it up (webhook, email, schedule, chat, etc.)
- **Actions**: What it does (send email, update sheet, post to Slack, etc.)
- **Model**: GPT-4 (smart, expensive), Claude Sonnet (balanced), Gemini Flash (fast, cheap)

### Step 2: Create the Agent
**Option A — Natural Language (recommended)**:
1. Click **New Agent** at https://app.lindy.ai
2. Describe your agent in plain English:
   ```
   When a customer emails support@company.com, classify the email as
   billing/technical/general, draft a response using our knowledge base,
   and post the classification to #support-triage in Slack
   ```
3. Agent Builder auto-generates trigger + action nodes

**Option B — Manual Build**:
1. Click **New Agent** > **Start from scratch**
2. Add trigger: Click **"+"** > Select trigger type
3. Add actions: Click **"+"** > Search for action
4. Connect nodes by dragging arrows between steps

### Step 3: Configure the Prompt
Open **Settings > Prompt**. Structure it with clear sections:
```
## Identity
You are a customer support classifier and responder for [Company].

## Instructions
1. Read the incoming email carefully
2. Classify into: billing, technical, or general
3. Search the knowledge base for relevant answers
4. Draft a professional response using the KB results
5. If no KB match found, escalate to human

## Constraints
- Never promise refunds or credits without human approval
- Keep responses under 200 words
- Always include ticket reference number
```

**Prompt best practices** (from Lindy docs):
- Use action-oriented language (imperatives)
- Break complex logic into numbered steps
- Include few-shot examples for consistent formatting
- Add constraints to prevent unwanted behavior

### Step 4: Add Conditions (Branching Logic)
1. Click **"+"** > **Condition**
2. Write natural language condition: `"Go down this path if the email is about billing"`
3. Add multiple branches for different classifications
4. Enable **"Force the agent to select a branch"** for deterministic routing

### Step 5: Configure Actions
For each action, set field modes:

**Auto mode** — Agent infers the value from all previous step data:
```
Best for: predictable mappings where field names align
```

**AI Prompt mode** — Give natural language instructions:
```
Summarize the email in 2 sentences, then include the classification.
Reference: {{email_received.body}}
```

**Set Manually mode** — Exact value, no AI:
```
Channel: #support-triage
```

### Step 6: Add Knowledge Base (Optional)
1. Go to **Settings > Knowledge Base**
2. Add sources: PDF, DOCX, Google Drive, Notion, websites
3. Configure search:
   - **Max Results**: 4 (default) to 10
   - **Search Fuzziness**: 0 (keyword) to 100 (semantic, recommended)
4. Agent auto-searches KB when relevant to the task

### Step 7: Test the Agent
1. Use the **Test** button in the workflow editor
2. Provide sample input matching your trigger type
3. Review each step's output in the task detail view
4. Iterate on prompt and action configuration

## Trigger Types Reference

| Trigger | Use Case | Configuration |
|---------|----------|---------------|
| **Webhook Received** | External API calls | URL + secret key |
| **Email Received** | Inbox automation | Gmail/Outlook + label filters |
| **Schedule** | Recurring tasks | Cron-style: daily, weekly, custom |
| **Chat Message** | Interactive bot | Lindy Chat or Embed widget |
| **Slack Message** | Team automation | Channel + keyword filters |
| **Agent Message** | Multi-agent delegation | Receives from other Lindies |
| **Calendar Event** | Meeting automation | Minutes offset (-30 = 30 min before) |
| **Form Submission** | Lead capture | Connected form integration |

## Action Categories

| Category | Actions |
|----------|---------|
| **Email** | Send Email, Draft Reply, Search Inbox, Add Label |
| **Slack** | Send Channel Message, Send DM, Thread Reply |
| **Sheets** | Update Spreadsheet, Get Document |
| **Calendar** | Create Event, Reschedule, Cancel |
| **Knowledge** | Search Knowledge Base, Resync KB |
| **Code** | Run Code (Python/JS in E2B sandbox) |
| **Web** | HTTP Request, Web Search, Website Crawler |
| **Memory** | Read/Create/Update/Delete Memory |
| **Phone** | Make Call, Transfer Call, End Call |
| **Agent** | Agent Send Message (delegation) |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "No trigger configured" | Agent has no trigger | Add at least one trigger node |
| Action fails silently | Wrong field mode | Switch to AI Prompt or Set Manually |
| KB returns no results | Fuzziness too low | Increase to 100 (semantic search) |
| Condition always picks same path | Ambiguous prompt | Make conditions more specific |
| Agent loops indefinitely | No exit condition | Add measurable exit criteria |

## Resources
- [Lindy Introduction](https://docs.lindy.ai/fundamentals/lindy-101/introduction)
- [Triggers Documentation](https://docs.lindy.ai/fundamentals/lindy-101/triggers)
- [Actions Documentation](https://docs.lindy.ai/fundamentals/lindy-101/actions)
- [Prompt Guide](https://docs.lindy.ai/fundamentals/lindy-101/prompt-guide)

## Next Steps
Proceed to `lindy-core-workflow-b` for triggers, automation, and multi-agent delegation.
