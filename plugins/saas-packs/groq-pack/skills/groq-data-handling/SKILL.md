---
name: groq-data-handling
description: |
  Implement prompt sanitization, PII redaction, response filtering, and
  usage tracking for Groq API integrations.
  Trigger with phrases like "groq data", "groq PII",
  "groq GDPR", "groq data retention", "groq privacy", "groq compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, groq, compliance]

---
# Groq Data Handling

## Overview
Manage data flowing through Groq's inference API. Covers prompt sanitization before sending to Groq, response filtering after receiving, PII redaction, conversation audit logging, and token usage tracking. Key fact: Groq does not use API data for model training ([Groq Privacy Policy](https://groq.com/privacy-policy/)).

## Groq Data Policy
- Groq does **not** train on API request/response data
- Prompts and completions are processed and discarded
- Groq may temporarily log requests for abuse prevention
- For enterprise: contact Groq for DPA and SOC 2 compliance details

## Instructions

### Step 1: Prompt Sanitization Layer
```typescript
import Groq from "groq-sdk";

const groq = new Groq();

interface RedactionRule {
  name: string;
  pattern: RegExp;
  replacement: string;
}

const PII_RULES: RedactionRule[] = [
  { name: "email", pattern: /\b[\w.+-]+@[\w-]+\.[\w.]+\b/g, replacement: "[EMAIL]" },
  { name: "phone", pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, replacement: "[PHONE]" },
  { name: "ssn", pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: "[SSN]" },
  { name: "credit_card", pattern: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g, replacement: "[CARD]" },
  { name: "ip_address", pattern: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, replacement: "[IP]" },
];

function sanitizeText(text: string): { sanitized: string; redactedTypes: string[] } {
  let sanitized = text;
  const redactedTypes: string[] = [];

  for (const rule of PII_RULES) {
    if (rule.pattern.test(sanitized)) {
      redactedTypes.push(rule.name);
      sanitized = sanitized.replace(rule.pattern, rule.replacement);
    }
  }

  return { sanitized, redactedTypes };
}

function sanitizeMessages(messages: any[]): { messages: any[]; hadPII: boolean } {
  let hadPII = false;
  const sanitized = messages.map((m) => {
    if (typeof m.content !== "string") return m;
    const { sanitized: text, redactedTypes } = sanitizeText(m.content);
    if (redactedTypes.length > 0) hadPII = true;
    return { ...m, content: text };
  });

  return { messages: sanitized, hadPII };
}
```

### Step 2: Safe Completion Wrapper
```typescript
async function safeCompletion(
  messages: any[],
  model = "llama-3.3-70b-versatile",
  options?: { maxTokens?: number }
) {
  // Sanitize input
  const { messages: sanitized, hadPII } = sanitizeMessages(messages);
  if (hadPII) {
    console.warn("[groq-data] PII detected and redacted before sending to Groq API");
  }

  // Call Groq
  const completion = await groq.chat.completions.create({
    model,
    messages: sanitized,
    max_tokens: options?.maxTokens ?? 1024,
  });

  // Filter response
  const responseContent = completion.choices[0].message.content || "";
  const { sanitized: filteredContent, redactedTypes } = sanitizeText(responseContent);

  if (redactedTypes.length > 0) {
    console.warn(`[groq-data] Response contained PII: ${redactedTypes.join(", ")}`);
  }

  return {
    ...completion,
    choices: [{
      ...completion.choices[0],
      message: {
        ...completion.choices[0].message,
        content: filteredContent,
      },
    }],
  };
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
  estimatedCostUsd: number;
  sessionId?: string;
}

const COST_PER_1M: Record<string, { input: number; output: number }> = {
  "llama-3.1-8b-instant": { input: 0.05, output: 0.08 },
  "llama-3.3-70b-versatile": { input: 0.59, output: 0.79 },
  "llama-3.3-70b-specdec": { input: 0.59, output: 0.99 },
  "meta-llama/llama-4-scout-17b-16e-instruct": { input: 0.11, output: 0.34 },
};

function calculateCost(model: string, usage: any): number {
  const pricing = COST_PER_1M[model] || { input: 0.10, output: 0.10 };
  return (
    (usage.prompt_tokens / 1_000_000) * pricing.input +
    (usage.completion_tokens / 1_000_000) * pricing.output
  );
}

function trackUsage(model: string, usage: any, sessionId?: string): UsageRecord {
  const record: UsageRecord = {
    timestamp: new Date().toISOString(),
    model,
    promptTokens: usage.prompt_tokens,
    completionTokens: usage.completion_tokens,
    totalTokens: usage.total_tokens,
    estimatedCostUsd: calculateCost(model, usage),
    sessionId,
  };

  // Store in your preferred backend
  console.log(JSON.stringify({ type: "groq_usage", ...record }));
  return record;
}
```

### Step 4: Audit-Logged Completion
```typescript
interface AuditLog {
  timestamp: string;
  sessionId: string;
  model: string;
  promptHash: string;        // Hash of input (not the input itself)
  piiDetected: boolean;
  responseFiltered: boolean;
  usage: UsageRecord;
}

async function auditedCompletion(
  sessionId: string,
  messages: any[],
  model = "llama-3.3-70b-versatile"
): Promise<{ content: string; audit: AuditLog }> {
  const { messages: sanitized, hadPII } = sanitizeMessages(messages);

  const completion = await groq.chat.completions.create({
    model,
    messages: sanitized,
  });

  const responseContent = completion.choices[0].message.content || "";
  const { sanitized: filtered, redactedTypes } = sanitizeText(responseContent);
  const usage = trackUsage(model, completion.usage, sessionId);

  const audit: AuditLog = {
    timestamp: new Date().toISOString(),
    sessionId,
    model,
    promptHash: createHash("sha256")
      .update(sanitized.map((m: any) => m.content).join("|"))
      .digest("hex"),
    piiDetected: hadPII,
    responseFiltered: redactedTypes.length > 0,
    usage,
  };

  // Log audit entry (don't log prompt content, only hash)
  console.log(JSON.stringify({ type: "groq_audit", ...audit }));

  return { content: filtered, audit };
}
```

### Step 5: Content Safety Check
```typescript
// Use Groq's Llama Guard for content moderation
async function moderateContent(text: string): Promise<{
  safe: boolean;
  categories: string[];
}> {
  const completion = await groq.chat.completions.create({
    model: "meta-llama/llama-guard-4-12b",
    messages: [{ role: "user", content: text }],
    max_tokens: 100,
  });

  const response = completion.choices[0].message.content || "";
  const safe = response.trim().toLowerCase().startsWith("safe");

  return {
    safe,
    categories: safe ? [] : response.split("\n").slice(1).map((l) => l.trim()).filter(Boolean),
  };
}
```

### Step 6: Daily Cost Report
```typescript
function generateCostReport(records: UsageRecord[]) {
  const totalCost = records.reduce((sum, r) => sum + r.estimatedCostUsd, 0);
  const totalTokens = records.reduce((sum, r) => sum + r.totalTokens, 0);

  const byModel: Record<string, { cost: number; tokens: number; calls: number }> = {};
  for (const r of records) {
    if (!byModel[r.model]) byModel[r.model] = { cost: 0, tokens: 0, calls: 0 };
    byModel[r.model].cost += r.estimatedCostUsd;
    byModel[r.model].tokens += r.totalTokens;
    byModel[r.model].calls++;
  }

  return {
    totalCost: `$${totalCost.toFixed(4)}`,
    totalTokens,
    totalCalls: records.length,
    byModel: Object.fromEntries(
      Object.entries(byModel).map(([model, data]) => [
        model,
        { cost: `$${data.cost.toFixed(4)}`, tokens: data.tokens, calls: data.calls },
      ])
    ),
  };
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII leaks in response | Model echoes sensitive input | Apply response filtering on all completions |
| Cost spike | 70B model for all requests | Route simple tasks to 8B |
| Missing usage data | Streaming mode | Use non-streaming for tracked requests, or estimate |
| Audit gaps | Not all code paths use wrapper | Lint rule: ban direct `groq.chat.completions.create` |

## Resources
- [Groq Privacy Policy](https://groq.com/privacy-policy/)
- [Groq Pricing](https://groq.com/pricing)
- [Llama Guard (content moderation)](https://console.groq.com/docs/model/meta-llama/llama-guard-4-12b)

## Next Steps
For enterprise access controls, see `groq-enterprise-rbac`.
