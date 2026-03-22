---
name: mistral-data-handling
description: |
  Implement Mistral AI PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Mistral AI integrations.
  Trigger with phrases like "mistral data", "mistral PII",
  "mistral GDPR", "mistral data retention", "mistral privacy".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, mistral, compliance]

---
# Mistral Data Handling

## Overview
Manage data flows through Mistral AI APIs with PII redaction, audit logging, fine-tuning dataset sanitization, and conversation retention policies. Mistral's data policy: API requests on La Plateforme are **not** used for training by default. Self-deployed models give full data sovereignty.

## Prerequisites
- Mistral API key configured
- Understanding of data classification (PII, PHI, PCI)
- Logging infrastructure for audit trails

## Instructions

### Step 1: PII Redaction Before API Calls

```typescript
interface RedactionRule {
  pattern: RegExp;
  replacement: string;
  type: string;
}

const PII_RULES: RedactionRule[] = [
  { pattern: /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi, replacement: '[EMAIL]', type: 'email' },
  { pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, replacement: '[PHONE]', type: 'phone' },
  { pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: '[SSN]', type: 'ssn' },
  { pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, replacement: '[CARD]', type: 'credit_card' },
  { pattern: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, replacement: '[IP]', type: 'ip_address' },
];

function redactPII(text: string): { cleaned: string; redactions: string[] } {
  const redactions: string[] = [];
  let cleaned = text;

  for (const rule of PII_RULES) {
    const matches = cleaned.match(rule.pattern);
    if (matches) {
      redactions.push(...matches.map(m => `${rule.type}: ${m.slice(0, 4)}***`));
      cleaned = cleaned.replace(rule.pattern, rule.replacement);
    }
  }
  return { cleaned, redactions };
}
```

### Step 2: Safe Mistral API Wrapper

```typescript
import { Mistral } from '@mistralai/mistralai';

const client = new Mistral({ apiKey: process.env.MISTRAL_API_KEY });

async function safeChatCompletion(
  messages: Array<{ role: string; content: string }>,
  options: { redactPII?: boolean; model?: string; auditLog?: boolean } = {},
) {
  const processed = messages.map(msg => {
    if (options.redactPII !== false) {
      const { cleaned, redactions } = redactPII(msg.content);
      if (redactions.length > 0 && options.auditLog) {
        console.warn(`Redacted ${redactions.length} PII items from ${msg.role} message`);
      }
      return { ...msg, content: cleaned };
    }
    return msg;
  });

  const response = await client.chat.complete({
    model: options.model ?? 'mistral-small-latest',
    messages: processed,
  });

  // Optionally redact PII in output too
  const output = response.choices?.[0]?.message?.content ?? '';
  if (options.redactPII !== false) {
    const { cleaned } = redactPII(output);
    if (response.choices?.[0]?.message) {
      response.choices[0].message.content = cleaned;
    }
  }

  return response;
}
```

### Step 3: Fine-Tuning Dataset Sanitization

Mistral fine-tuning requires JSONL files. Sanitize before uploading:

```typescript
import { createReadStream, createWriteStream } from 'fs';
import { createInterface } from 'readline';

async function sanitizeTrainingData(inputPath: string, outputPath: string) {
  const rl = createInterface({ input: createReadStream(inputPath) });
  const out = createWriteStream(outputPath);
  let lines = 0, redacted = 0;

  for await (const line of rl) {
    const record = JSON.parse(line);
    const sanitized = record.messages.map((msg: any) => {
      const { cleaned, redactions } = redactPII(msg.content);
      if (redactions.length > 0) redacted++;
      return { ...msg, content: cleaned };
    });

    out.write(JSON.stringify({ messages: sanitized }) + '\n');
    lines++;
  }

  out.end();
  console.log(`Processed ${lines} training examples, redacted PII in ${redacted}`);
  return { lines, redacted };
}
```

### Step 4: Conversation History with TTL

```typescript
class ConversationStore {
  private store = new Map<string, { messages: any[]; createdAt: number }>();
  private maxAgeMins: number;
  private maxMessages: number;

  constructor(maxAgeMins = 60, maxMessages = 100) {
    this.maxAgeMins = maxAgeMins;
    this.maxMessages = maxMessages;
  }

  get(sessionId: string): any[] {
    const entry = this.store.get(sessionId);
    if (!entry) return [];

    // Auto-expire
    if (Date.now() - entry.createdAt > this.maxAgeMins * 60_000) {
      this.store.delete(sessionId);
      return [];
    }

    return entry.messages;
  }

  append(sessionId: string, message: any): void {
    const entry = this.store.get(sessionId) ?? { messages: [], createdAt: Date.now() };
    entry.messages.push(message);

    // Cap message count
    if (entry.messages.length > this.maxMessages) {
      const system = entry.messages[0]?.role === 'system' ? [entry.messages[0]] : [];
      entry.messages = [...system, ...entry.messages.slice(-this.maxMessages)];
    }

    this.store.set(sessionId, entry);
  }

  destroy(sessionId: string): void {
    this.store.delete(sessionId);
  }

  // GDPR right-to-erasure
  eraseUser(userId: string): number {
    let count = 0;
    for (const [key] of this.store) {
      if (key.startsWith(userId)) {
        this.store.delete(key);
        count++;
      }
    }
    return count;
  }
}
```

### Step 5: Audit Logging

```typescript
interface AuditEntry {
  timestamp: string;
  sessionId: string;
  model: string;
  inputChars: number;
  outputChars: number;
  piiRedacted: number;
  tokensUsed: { prompt: number; completion: number };
}

function logAudit(entry: AuditEntry): void {
  // Log metadata only — never log actual message content
  console.log(JSON.stringify({
    ...entry,
    // Intentionally exclude message content for compliance
  }));
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII leak to API | Regex missed pattern | Add domain-specific rules (e.g., patient IDs) |
| Fine-tune rejected | Unsanitized data in JSONL | Run sanitization before `client.files.upload()` |
| Conversation too long | No retention policy | Set max age and message count limits |
| GDPR request | Right to erasure | Implement `eraseUser()` across all stores |

## Examples

### Safe Embedding Generation
```typescript
async function safeEmbed(texts: string[]) {
  const cleaned = texts.map(t => redactPII(t).cleaned);
  return client.embeddings.create({
    model: 'mistral-embed',
    inputs: cleaned,
  });
}
```

### Batch API with PII Redaction
```python
import json

def sanitize_batch_file(input_path: str, output_path: str):
    """Sanitize a Mistral batch JSONL file before submission."""
    with open(input_path) as f_in, open(output_path, "w") as f_out:
        for line in f_in:
            record = json.loads(line)
            for msg in record["body"]["messages"]:
                msg["content"] = redact_pii(msg["content"])
            f_out.write(json.dumps(record) + "\n")
```

## Resources
- [Mistral Data Policy](https://docs.mistral.ai/deployment/ai-studio/)
- [Fine-Tuning Guide](https://docs.mistral.ai/capabilities/finetuning/)
- [Batch Inference](https://docs.mistral.ai/capabilities/batch/)
- [GDPR Compliance](https://mistral.ai/privacy/)

## Output
- PII redaction layer for all API calls
- Safe chat wrapper with audit logging
- Fine-tuning dataset sanitization pipeline
- Conversation store with TTL and GDPR erasure
