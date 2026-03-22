---
name: cohere-data-handling
description: |
  Implement data privacy for Cohere API calls with PII redaction and compliance.
  Use when handling sensitive data, implementing PII redaction before API calls,
  or ensuring GDPR/CCPA compliance with Cohere integrations.
  Trigger with phrases like "cohere data", "cohere PII",
  "cohere GDPR", "cohere data retention", "cohere privacy", "cohere redact".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, ai, nlp, cohere]
compatible-with: claude-code
---

# Cohere Data Handling

## Overview
Handle sensitive data when calling Cohere APIs. Cohere processes text server-side for Chat, Embed, Rerank, and Classify — any PII in your input reaches their servers. This skill covers pre-call redaction, post-call scrubbing, and compliance patterns.

## Prerequisites
- Understanding of GDPR/CCPA requirements
- `cohere-ai` SDK installed
- Database for audit logging

## Data Flow Awareness

```
Your App → [PII Redaction] → Cohere API → [Response Scrubbing] → Your App → User

Key point: Everything you send to cohere.chat(), cohere.embed(), etc.
is processed on Cohere's servers. Redact BEFORE the API call.
```

## Instructions

### Step 1: PII Detection

```typescript
interface PIIFinding {
  type: string;
  match: string;
  start: number;
  end: number;
}

const PII_PATTERNS: Array<{ type: string; regex: RegExp }> = [
  { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
  { type: 'phone', regex: /\b(\+\d{1,3}[-.]?)?\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
  { type: 'ssn', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
  { type: 'credit_card', regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
  { type: 'ip_address', regex: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g },
];

function detectPII(text: string): PIIFinding[] {
  const findings: PIIFinding[] = [];
  for (const { type, regex } of PII_PATTERNS) {
    for (const match of text.matchAll(new RegExp(regex))) {
      findings.push({
        type,
        match: match[0],
        start: match.index!,
        end: match.index! + match[0].length,
      });
    }
  }
  return findings;
}
```

### Step 2: Pre-Call Redaction

```typescript
function redactPII(text: string): { redacted: string; map: Map<string, string> } {
  const map = new Map<string, string>();
  let redacted = text;
  let counter = 0;

  for (const { type, regex } of PII_PATTERNS) {
    redacted = redacted.replace(new RegExp(regex), (match) => {
      const placeholder = `[${type.toUpperCase()}_${counter++}]`;
      map.set(placeholder, match);
      return placeholder;
    });
  }

  return { redacted, map };
}

// Usage: redact before sending to Cohere
async function safeCohereChat(userInput: string) {
  const { redacted, map } = redactPII(userInput);

  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: redacted }],
  });

  // Optionally restore PII in response (for internal use only)
  let answer = response.message?.content?.[0]?.text ?? '';
  for (const [placeholder, original] of map) {
    answer = answer.replace(placeholder, original);
  }

  return answer;
}
```

### Step 3: Safe Embedding

```typescript
// Embeddings are stored long-term in vector DBs — ensure no PII
async function safeEmbed(texts: string[]): Promise<number[][]> {
  // Check for PII before embedding
  for (const text of texts) {
    const pii = detectPII(text);
    if (pii.length > 0) {
      console.warn(`PII detected in embed input: ${pii.map(p => p.type).join(', ')}`);
      // Option 1: Redact and embed
      // Option 2: Reject and throw
      throw new Error(`PII found in embedding input: ${pii.map(p => p.type).join(', ')}`);
    }
  }

  return cohere.embed({
    model: 'embed-v4.0',
    texts,
    inputType: 'search_document',
    embeddingTypes: ['float'],
  }).then(r => r.embeddings.float);
}
```

### Step 4: Classify with Data Minimization

```typescript
// Classify endpoint receives text + examples — minimize both
async function safeClassify(inputs: string[]) {
  // Redact PII from classification inputs
  const safeInputs = inputs.map(text => redactPII(text).redacted);

  return cohere.classify({
    model: 'embed-english-v3.0',
    inputs: safeInputs,
    examples: [
      // Examples should never contain real PII
      { text: 'This product is great', label: 'positive' },
      { text: 'Amazing experience', label: 'positive' },
      { text: 'Terrible service', label: 'negative' },
      { text: 'Very disappointed', label: 'negative' },
    ],
  });
}
```

### Step 5: Audit Logging

```typescript
interface CohereAuditEntry {
  timestamp: Date;
  endpoint: string;
  model: string;
  piiDetected: string[];
  redacted: boolean;
  tokensUsed: { input: number; output: number };
  userId?: string;
}

async function auditCohereCall(entry: CohereAuditEntry): Promise<void> {
  // Log to database (not console — structured storage)
  await db.cohereAudit.insert({
    ...entry,
    // Never log the actual API input/output — only metadata
  });
}

// Usage
async function auditedChat(userId: string, message: string) {
  const pii = detectPII(message);
  const { redacted } = redactPII(message);

  const response = await cohere.chat({
    model: 'command-a-03-2025',
    messages: [{ role: 'user', content: redacted }],
  });

  await auditCohereCall({
    timestamp: new Date(),
    endpoint: 'chat',
    model: 'command-a-03-2025',
    piiDetected: pii.map(p => p.type),
    redacted: pii.length > 0,
    tokensUsed: {
      input: response.usage?.billedUnits?.inputTokens ?? 0,
      output: response.usage?.billedUnits?.outputTokens ?? 0,
    },
    userId,
  });

  return response;
}
```

### Step 6: Safety Modes for Content Filtering

```typescript
// Cohere's built-in safety modes (separate from PII — these handle harmful content)
await cohere.chat({
  model: 'command-a-03-2025',
  messages: [{ role: 'user', content: userInput }],
  safetyMode: 'STRICT',  // Maximum content filtering
  // Options: 'CONTEXTUAL' (default), 'STRICT', 'OFF'
  // Note: Not configurable when using tools or documents
});
```

## Data Retention Guidelines

| Data | Retention | Action |
|------|-----------|--------|
| API request logs (redacted) | 30 days | Auto-delete |
| Audit entries | 7 years | Archive to cold storage |
| Cached embeddings | Until source changes | Invalidate on update |
| Cohere API responses | Do not persist | Process in memory only |
| PII mappings | Per-request only | Never persist |

## Compliance Checklist

- [ ] PII redacted before all Cohere API calls
- [ ] Embeddings verified PII-free before vector DB storage
- [ ] Audit trail for all API calls with PII metadata
- [ ] Safety mode set to STRICT for user-facing applications
- [ ] API responses not persisted (processed in memory)
- [ ] Data retention policy enforced with automated cleanup
- [ ] Classify examples use synthetic data (no real PII)

## Output
- PII detection and redaction pipeline
- Safe wrappers for Chat, Embed, and Classify
- Audit logging with PII metadata (not content)
- Data retention policy with automated cleanup

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII in embeddings | Missing pre-check | Add detectPII before embed |
| Redaction breaks context | Over-aggressive regex | Use domain-specific patterns |
| Audit gap | Async logging failed | Use sync fallback |
| Safety mode ignored | Used with tools/docs | Separate safety from RAG calls |

## Resources
- [Cohere Safety Modes](https://docs.cohere.com/docs/safety-modes)
- [Cohere Privacy Policy](https://cohere.com/privacy)
- [GDPR Developer Guide](https://gdpr.eu/developers/)

## Next Steps
For enterprise access control, see `cohere-enterprise-rbac`.
