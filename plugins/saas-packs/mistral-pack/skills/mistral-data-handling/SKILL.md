---
name: mistral-data-handling
description: |
  Implement Mistral AI PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Mistral AI integrations.
  Trigger with phrases like "mistral data", "mistral PII",
  "mistral GDPR", "mistral data retention", "mistral privacy", "mistral CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral Data Handling

## Overview
Manage data flows through Mistral AI APIs safely. Covers input sanitization before sending to models, response filtering, conversation history management, and fine-tuning dataset preparation with PII redaction.

## Prerequisites
- Mistral API key
- `@mistralai/mistralai` SDK installed
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
      redactions.push(...matches.map(m => `${rule.type}: ${m}`));
      cleaned = cleaned.replace(rule.pattern, rule.replacement);
    }
  }

  return { cleaned, redactions };
}
```

### Step 2: Safe Mistral API Wrapper
```typescript
import { Mistral } from '@mistralai/mistralai';

const mistral = new Mistral({ apiKey: process.env.MISTRAL_API_KEY! });

async function safeChatCompletion(
  messages: Array<{ role: string; content: string }>,
  options?: { redactPII?: boolean; model?: string }
) {
  const processedMessages = messages.map(msg => {
    if (options?.redactPII !== false) {
      const { cleaned, redactions } = redactPII(msg.content);
      if (redactions.length > 0) {
        console.warn(`Redacted ${redactions.length} PII items from ${msg.role} message`);
      }
      return { ...msg, content: cleaned };
    }
    return msg;
  });

  return mistral.chat.complete({
    model: options?.model || 'mistral-small-latest',
    messages: processedMessages,
  });
}
```

### Step 3: Fine-Tuning Dataset Sanitization
```typescript
import { createReadStream, createWriteStream } from 'fs';
import { createInterface } from 'readline';

async function sanitizeTrainingData(
  inputPath: string,
  outputPath: string
) {
  const input = createInterface({ input: createReadStream(inputPath) });
  const output = createWriteStream(outputPath);
  let lineCount = 0;
  let redactedCount = 0;

  for await (const line of input) {
    const record = JSON.parse(line);
    const messages = record.messages.map((msg: any) => {
      const { cleaned, redactions } = redactPII(msg.content);
      if (redactions.length > 0) redactedCount++;
      return { ...msg, content: cleaned };
    });

    output.write(JSON.stringify({ messages }) + '\n');
    lineCount++;
  }

  output.end();
  return { lineCount, redactedCount };
}
```

### Step 4: Conversation History with Retention
```typescript
interface ConversationStore {
  get(sessionId: string): Promise<any[]>;
  append(sessionId: string, message: any): Promise<void>;
  expire(sessionId: string): Promise<void>;
}

class TimeBoundConversationStore implements ConversationStore {
  private store = new Map<string, { messages: any[]; createdAt: number }>();
  private maxAgeMins: number;

  constructor(maxAgeMins = 60) {
    this.maxAgeMins = maxAgeMins;
  }

  async get(sessionId: string) {
    const entry = this.store.get(sessionId);
    if (!entry) return [];

    const ageMs = Date.now() - entry.createdAt;
    if (ageMs > this.maxAgeMins * 60 * 1000) {  # 1000: 1 second in ms
      this.store.delete(sessionId);
      return [];
    }

    return entry.messages;
  }

  async append(sessionId: string, message: any) {
    const entry = this.store.get(sessionId) || { messages: [], createdAt: Date.now() };
    entry.messages.push(message);
    this.store.set(sessionId, entry);
  }

  async expire(sessionId: string) {
    this.store.delete(sessionId);
  }
}
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII leaks to API | Regex missed pattern | Add custom rules for domain-specific PII |
| Fine-tune rejected | Unsanitized data | Run sanitization before upload |
| Conversation too long | No retention policy | Set max age and message count limits |
| Audit trail gaps | No redaction logging | Log all redaction events |

## Examples

### Safe Embedding Generation
```typescript
async function safeEmbed(texts: string[]) {
  const cleaned = texts.map(t => redactPII(t).cleaned);
  return mistral.embeddings.create({
    model: 'mistral-embed',
    inputs: cleaned,
  });
}
```

## Resources
- [Mistral AI Data Policy](https://docs.mistral.ai/capabilities/data-policy/)
- [Mistral Fine-Tuning Guide](https://docs.mistral.ai/capabilities/finetuning/)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale