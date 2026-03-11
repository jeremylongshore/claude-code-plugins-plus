---
name: groq-data-handling
description: |
  Implement Groq PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Groq integrations.
  Trigger with phrases like "groq data", "groq PII",
  "groq GDPR", "groq data retention", "groq privacy", "groq CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Groq Data Handling

## Overview
Manage data flowing through Groq's ultra-fast LPU inference. Covers prompt sanitization, response filtering, conversation logging with PII redaction, and token usage tracking for cost management.

## Prerequisites
- Groq API key
- `groq-sdk` npm package
- Understanding of LLM data flow (prompts in, completions out)
- Logging infrastructure for audit

## Instructions

### Step 1: Prompt Sanitization Layer
```typescript
import Groq from 'groq-sdk';

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });

const PII_REDACTORS = [
  { pattern: /\b[\w.+-]+@[\w-]+\.[\w.]+\b/g, replace: '[EMAIL]' },
  { pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, replace: '[PHONE]' },
  { pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replace: '[SSN]' },
];

function sanitizePrompt(text: string): { text: string; hadPII: boolean } {
  let hadPII = false;
  let sanitized = text;

  for (const { pattern, replace } of PII_REDACTORS) {
    if (pattern.test(sanitized)) hadPII = true;
    sanitized = sanitized.replace(pattern, replace);
  }

  return { text: sanitized, hadPII };
}

async function safeChatCompletion(messages: any[], model = 'llama-3.1-8b-instant') {
  const sanitizedMessages = messages.map(m => ({
    ...m,
    content: sanitizePrompt(m.content).text,
  }));

  return groq.chat.completions.create({ model, messages: sanitizedMessages });
}
```

### Step 2: Response Content Filtering
```typescript
interface FilterResult {
  content: string;
  filtered: boolean;
  reasons: string[];
}

function filterResponse(content: string): FilterResult {
  const reasons: string[] = [];

  // Check for leaked PII patterns in response
  for (const { pattern, replace } of PII_REDACTORS) {
    if (pattern.test(content)) {
      reasons.push(`Response contained ${replace} pattern`);
      content = content.replace(pattern, replace);
    }
  }

  // Check for code injection patterns
  if (/<script|javascript:|onclick=/i.test(content)) {
    reasons.push('Response contained script injection');
    content = content.replace(/<script[\s\S]*?<\/script>/gi, '[REMOVED]');
  }

  return { content, filtered: reasons.length > 0, reasons };
}

async function safeCompletion(messages: any[]) {
  const result = await safeChatCompletion(messages);
  const raw = result.choices[0].message.content || '';
  const filtered = filterResponse(raw);

  if (filtered.filtered) {
    console.warn('Response filtered:', filtered.reasons);
  }

  return { ...result, choices: [{ ...result.choices[0], message: { ...result.choices[0].message, content: filtered.content } }] };
}
```

### Step 3: Token Usage Tracking
```typescript
interface UsageRecord {
  timestamp: string;
  model: string;
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  estimatedCost: number;
}

const COST_PER_MILLION: Record<string, { input: number; output: number }> = {
  'llama-3.1-8b-instant': { input: 0.05, output: 0.08 },
  'llama-3.3-70b-versatile': { input: 0.59, output: 0.79 },
  'mixtral-8x7b-32768': { input: 0.24, output: 0.24 },  # 32768 = configured value
};

function trackUsage(model: string, usage: any): UsageRecord {
  const costs = COST_PER_MILLION[model] || { input: 0.50, output: 0.50 };

  return {
    timestamp: new Date().toISOString(),
    model,
    promptTokens: usage.prompt_tokens,
    completionTokens: usage.completion_tokens,
    totalTokens: usage.total_tokens,
    estimatedCost:
      (usage.prompt_tokens / 1_000_000) * costs.input +
      (usage.completion_tokens / 1_000_000) * costs.output,
  };
}
```

### Step 4: Conversation Logging with Redaction
```typescript
interface AuditLog {
  sessionId: string;
  timestamp: string;
  model: string;
  promptRedacted: string;
  responseRedacted: string;
  tokenUsage: UsageRecord;
}

async function loggedCompletion(
  sessionId: string,
  messages: any[],
  model = 'llama-3.1-8b-instant'
): Promise<{ response: string; log: AuditLog }> {
  const sanitized = messages.map(m => ({
    ...m,
    content: sanitizePrompt(m.content).text,
  }));

  const result = await groq.chat.completions.create({ model, messages: sanitized });
  const response = filterResponse(result.choices[0].message.content || '');
  const usage = trackUsage(model, result.usage);

  const log: AuditLog = {
    sessionId,
    timestamp: new Date().toISOString(),
    model,
    promptRedacted: sanitized.map(m => m.content).join(' | '),
    responseRedacted: response.content,
    tokenUsage: usage,
  };

  return { response: response.content, log };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in responses | Model echoed sensitive input | Apply response filtering |
| Cost spike | Using 70b model for all requests | Route simple tasks to 8b model |
| Missing usage data | Stream mode has no usage object | Track token estimates manually for streams |
| Audit gaps | Logging not on all paths | Use `loggedCompletion` wrapper everywhere |

## Examples

### Daily Cost Report
```typescript
function dailyCostReport(logs: AuditLog[]) {
  const totalCost = logs.reduce((s, l) => s + l.tokenUsage.estimatedCost, 0);
  const byModel = logs.reduce((acc, l) => {
    acc[l.tokenUsage.model] = (acc[l.tokenUsage.model] || 0) + l.tokenUsage.estimatedCost;
    return acc;
  }, {} as Record<string, number>);

  return { totalCost: totalCost.toFixed(4), byModel };
}
```

## Resources
- [Groq Privacy Policy](https://groq.com/privacy-policy/)
- [Groq Pricing](https://console.groq.com/docs/pricing)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale