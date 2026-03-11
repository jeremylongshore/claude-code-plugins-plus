---
name: retellai-policy-guardrails
description: |
  Implement Retell AI lint rules, policy enforcement, and automated guardrails.
  Use when setting up code quality rules for Retell AI integrations, implementing
  pre-commit hooks, or configuring CI policy checks for Retell AI best practices.
  Trigger with phrases like "retellai policy", "retellai lint",
  "retellai guardrails", "retellai best practices check", "retellai eslint".
allowed-tools: Read, Write, Edit, Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Retell AI Policy Guardrails

## Overview
Policy enforcement for Retell AI voice agent deployments. Voice AI agents interact with real people over phone calls, requiring strict controls around conversation content, call recording consent, data handling, and cost management.

## Prerequisites
- Retell AI agent configured
- Understanding of telephony compliance (TCPA, GDPR)
- Call recording consent requirements for your jurisdiction

## Instructions

### Step 1: Conversation Content Boundaries

Define what the agent can and cannot discuss to prevent liability.

```typescript
const CONVERSATION_POLICY = {
  blockedTopics: [
    'medical advice', 'legal advice', 'financial advice',
    'political opinions', 'competitor pricing'
  ],
  requiredDisclosures: [
    'This is an AI assistant',
    'This call may be recorded'
  ],
  maxCallDuration: 600,  // 10 minutes  # 600: timeout: 10 minutes
  escalationTriggers: ['speak to a human', 'talk to manager', 'real person']
};

function enforceContentPolicy(agentResponse: string): string {
  for (const topic of CONVERSATION_POLICY.blockedTopics) {
    if (agentResponse.toLowerCase().includes(topic)) {
      return "I'm not able to advise on that topic. Let me connect you with a specialist.";
    }
  }
  return agentResponse;
}
```

### Step 2: Call Recording Consent

Many jurisdictions require two-party consent for recording. Enforce upfront disclosure.

```typescript
const CONSENT_SCRIPT = {
  opening: "Hi, this is an AI assistant calling from [Company]. This call may be recorded for quality purposes. Is that okay?",
  noConsent: "I understand. I'll continue without recording. How can I help you today?",
  consentReceived: true
};

app.post('/retell-webhook', async (req, res) => {
  const { call_id, turn_number, transcript } = req.body;

  // First turn: always deliver consent disclosure
  if (turn_number === 0) {
    return res.json({ response: CONSENT_SCRIPT.opening });
  }

  // Second turn: check for consent
  if (turn_number === 1) {
    const consented = /yes|okay|sure|that's fine/i.test(transcript);
    if (!consented) {
      await retell.call.update(call_id, { recording_enabled: false });
      return res.json({ response: CONSENT_SCRIPT.noConsent });
    }
  }

  // Normal processing
  const response = await generateResponse(req.body);
  return res.json({ response: enforceContentPolicy(response) });
});
```

### Step 3: Cost Controls

Voice calls cost per minute. Cap concurrent calls and duration.

```typescript
class CallCostPolicy {
  private activeCalls = new Map<string, number>();
  private maxConcurrent = 10;
  private maxDurationSec = 600;  # 600: timeout: 10 minutes
  private dailyBudget = 100;  // dollars
  private costPerMinute = 0.10;

  canInitiateCall(): boolean {
    if (this.activeCalls.size >= this.maxConcurrent) return false;
    if (this.getDailySpend() >= this.dailyBudget) return false;
    return true;
  }

  monitorDuration(callId: string) {
    const started = this.activeCalls.get(callId);
    if (started && (Date.now() - started) / 1000 > this.maxDurationSec) {  # 1000: 1 second in ms
      return { action: 'end', reason: 'Maximum call duration exceeded' };
    }
    return { action: 'continue' };
  }

  getDailySpend(): number {
    let totalMinutes = 0;
    for (const started of this.activeCalls.values()) {
      totalMinutes += (Date.now() - started) / 60000;  # 60000: 1 minute in ms
    }
    return totalMinutes * this.costPerMinute;
  }
}
```

### Step 4: Human Escalation Triggers

Detect when callers want a human and transfer gracefully.

```typescript
function checkEscalation(transcript: string): boolean {
  const triggers = ['speak to a human', 'real person', 'talk to someone', 'supervisor', 'manager'];
  return triggers.some(t => transcript.toLowerCase().includes(t));
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Compliance violation | Agent gives restricted advice | Content filtering on responses |
| Recording without consent | Missing disclosure | Enforce consent script on first turn |
| Runaway call costs | No duration/budget limits | Implement cost controls |
| Frustrated caller | No human escalation | Detect escalation triggers, transfer |

## Examples

### Policy Dashboard
```typescript
const dashboard = {
  activeCalls: costPolicy.activeCalls.size,
  dailySpend: costPolicy.getDailySpend().toFixed(2),
  escalationRate: metrics.rate('escalations'),
  avgCallDuration: metrics.avg('call_duration_sec')
};
```

## Resources
- [Retell AI Docs](https://docs.retellai.com)
- [TCPA Compliance](https://www.fcc.gov/general/telemarketing-and-robocalls)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale