---
name: lindy-reference-architecture
description: |
  Reference architectures for Lindy AI agent integrations.
  Use when designing systems, planning multi-agent architectures,
  or implementing production integration patterns.
  Trigger with phrases like "lindy architecture", "lindy design",
  "lindy system design", "lindy patterns", "lindy multi-agent".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, lindy-reference]

---
# Lindy Reference Architecture

## Overview
Production-ready architecture patterns for integrating Lindy AI agents into
applications. Covers webhook integration, multi-agent societies, event-driven
pipelines, and high-availability patterns.

## Prerequisites
- Understanding of Lindy agent model (triggers, actions, skills)
- Familiarity with webhook-based architectures
- Production requirements defined (throughput, latency, reliability)

## Architecture 1: Simple Webhook Integration
Single agent triggered by your application, results sent via callback.

```
┌─────────────┐       POST (webhook)       ┌──────────────┐
│  Your App   │ ─────────────────────────→  │ Lindy Agent  │
│             │                             │              │
│  /callback  │ ←─────────────────────────  │ HTTP Request │
│             │       POST (callback)       │   Action     │
└─────────────┘                             └──────────────┘
```

**Implementation**:
- Your app sends webhook with `callbackUrl` field
- Lindy agent processes and responds via Send POST Request to Callback
- Your app receives results asynchronously

**Best for**: Simple automations (email triage, lead scoring, content generation)

## Architecture 2: Event-Driven Pipeline
Multiple event sources feed agents through a central webhook router.

```
┌──────────┐
│ Stripe   │──webhook──┐
└──────────┘           │
                       ▼
┌──────────┐     ┌───────────┐     ┌──────────────┐
│ Shopify  │──→  │  Router   │──→  │ Lindy Agents │
└──────────┘     │  Service  │     │              │
                 └───────────┘     │ • Order Bot  │
┌──────────┐           ▲          │ • Support Bot│
│ Your App │──webhook──┘          │ • Analytics  │
└──────────┘                      └──────────────┘
```

**Implementation**:
```typescript
// Event router — maps events to specific Lindy agents
const agentWebhooks: Record<string, string> = {
  'order.created': process.env.LINDY_ORDER_AGENT_WEBHOOK!,
  'customer.support_request': process.env.LINDY_SUPPORT_AGENT_WEBHOOK!,
  'analytics.daily_report': process.env.LINDY_ANALYTICS_AGENT_WEBHOOK!,
};

app.post('/events', async (req, res) => {
  const { event, data } = req.body;
  const webhookUrl = agentWebhooks[event];

  if (!webhookUrl) {
    return res.status(400).json({ error: `Unknown event: ${event}` });
  }

  await fetch(webhookUrl, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.LINDY_WEBHOOK_SECRET}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ event, data, callbackUrl: `${BASE_URL}/callback` }),
  });

  res.json({ routed: true, agent: event });
});
```

**Best for**: Multiple event sources, different agents per event type

## Architecture 3: Multi-Agent Society (Delegation)
Specialized agents collaborate through Lindy's built-in delegation system.

```
┌─────────────────┐
│ Orchestrator    │
│ Lindy           │
│ (receives       │
│  initial task)  │
└───┬────────┬────┘
    │        │
    ▼        ▼
┌────────┐ ┌────────┐
│Research│ │Analysis│
│ Lindy  │ │ Lindy  │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌─────────────────┐
│ Writer Lindy    │
│ (synthesizes    │
│  final output)  │
└─────────────────┘
```

**Setup in Lindy**:
1. Create specialized agents with **Agent Message Received** triggers
2. Orchestrator uses **Agent Send Message** action to delegate
3. Each agent completes its specialty and sends results forward
4. Writer agent synthesizes and delivers final output

**Key decisions**:
| Decision | Option A | Option B |
|----------|---------|---------|
| Context passing | Full context (accurate, expensive) | Selective context (cheap, focused) |
| Error handling | Agent retries | Orchestrator retry logic |
| Parallelism | Sequential delegation | Parallel delegation with merge |

**Best for**: Complex tasks requiring multiple specialties (research + analysis + writing)

## Architecture 4: Scheduled Pipeline
Agents run on schedules, each feeding data to the next.

```
                    Schedule: Daily 6 AM
                         │
                         ▼
                  ┌──────────────┐
                  │ Data Fetch   │ Pulls from APIs/databases
                  │ Lindy        │
                  └──────┬───────┘
                         │ Agent Send Message
                         ▼
                  ┌──────────────┐
                  │ Analysis     │ Processes & summarizes
                  │ Lindy        │
                  └──────┬───────┘
                         │ Agent Send Message
                         ▼
                  ┌──────────────┐
                  │ Report       │ Formats & delivers
                  │ Lindy        │
                  │  → Slack     │
                  │  → Email     │
                  └──────────────┘
```

**Best for**: Daily reports, weekly digests, scheduled data processing

## Architecture 5: Chat + Knowledge Base
Agent deployed as customer-facing chatbot with RAG-powered responses.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Website     │     │ Lindy Agent  │     │ Knowledge    │
│  (Embed      │◀──▶ │              │◀──▶ │ Base         │
│   Widget)    │     │ Chat Trigger │     │ PDFs, Docs,  │
└──────────────┘     │ + KB Search  │     │ Websites     │
                     │ + Condition  │     └──────────────┘
                     │ + Escalate   │
                     └──────────────┘
                            │
                            ▼ (if escalation needed)
                     ┌──────────────┐
                     │ Slack DM to  │
                     │ human agent  │
                     └──────────────┘
```

**Deploy the embed widget**:
```html
<!-- Paste near end of <body> tag -->
<script src="https://embed.lindy.ai/widget.js"
  data-lindy-id="YOUR_AGENT_ID"></script>
```

**KB configuration**:
- Sources: Product docs, FAQ PDFs, knowledge articles
- Fuzziness: 100 (semantic search)
- Max Results: 5 (balance relevance vs context size)
- Auto-resync: every 24 hours

**Best for**: Customer support, FAQ bots, internal knowledge assistants

## Architecture Decision Matrix

| Pattern | Throughput | Latency | Complexity | Cost |
|---------|-----------|---------|-----------|------|
| Simple webhook | Low-Med | 2-15s | Low | Low |
| Event-driven pipeline | High | 5-30s | Medium | Medium |
| Multi-agent society | Low-Med | 30-120s | High | High |
| Scheduled pipeline | Batch | N/A | Medium | Predictable |
| Chat + KB | Interactive | 2-10s | Low-Med | Per-message |

## Error Handling

| Pattern | Failure Mode | Recovery |
|---------|-------------|----------|
| Simple webhook | Agent fails | Retry webhook with backoff |
| Event-driven | Router crash | Queue events, replay on recovery |
| Multi-agent | Delegation fails | Orchestrator retries or skips |
| Scheduled | Missed schedule | Next run catches up |
| Chat + KB | KB empty | Fallback to generic response + escalate |

## Resources
- [Lindy Introduction](https://docs.lindy.ai/fundamentals/lindy-101/introduction)
- [Delegation 101](https://www.lindy.ai/academy-lessons/delegation-101)
- [Building a Chatbot](https://www.lindy.ai/academy-lessons/building-a-chatbot-101)
- [Lindy Embed](https://www.lindy.ai/integrations/lindy-embed)

## Next Steps
Proceed to Flagship tier skills for enterprise features: multi-env, observability,
incident response, data handling, RBAC, and migration.
