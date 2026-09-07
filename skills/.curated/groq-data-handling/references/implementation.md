# Groq Data Handling — Full Implementation

The complete privacy pipeline. Each step layers onto the previous: sanitize
input → wrap the completion call → track usage → produce a hash-only audit
trail. All code is TypeScript against the `groq-sdk`.

## Step 1: Prompt Sanitization Layer

Redact PII from every message before it leaves your process. `sanitizeText`
runs a rule table and reports which categories it caught; `sanitizeMessages`
applies it across a full message array and flags whether any PII was present.

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

## Step 2: Safe Completion Wrapper

Wrap `groq.chat.completions.create` so both the input and the response pass
through the sanitizer. This is the function application code should call
instead of the raw SDK method.

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

## Step 3: Token Usage Tracking

Record every call's token counts and estimated cost. `COST_PER_1M` holds
per-model input/output pricing; update it when Groq changes rates.

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

## Step 4: Audit-Logged Completion

The top-level function: sanitize, call, filter, track, and emit an audit
entry that stores only a SHA-256 hash of the prompt — never the prompt text
itself — so the audit log carries no sensitive content.

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

`createHash` comes from Node's `crypto` module — add
`import { createHash } from "crypto";` at the top of the file.
