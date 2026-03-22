---
name: anthropic-data-handling
description: |
  Handle sensitive data with Claude — PII redaction, conversation management,
  context window optimization, and data retention policies.
  Trigger with "anthropic data privacy", "claude pii", "anthropic context window",
  "manage claude conversations", "anthropic data retention".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, data, privacy, context]
---

# Anthropic Data Handling

## Overview
Core functionality and patterns for anthropic-data-handling.


## Context Window Management
Claude models have a 200K token context window. Managing it efficiently is critical.

```typescript
// Count tokens before sending
const count = await client.messages.countTokens({
  model: 'claude-sonnet-4-20250514',
  messages,
  system: systemPrompt,
});

// Budget: 200K total - max_tokens (output) = available input
const MAX_CONTEXT = 200_000;
const MAX_OUTPUT = 4096;
const inputBudget = MAX_CONTEXT - MAX_OUTPUT;

if (count.input_tokens > inputBudget) {
  // Trim oldest messages, keep system prompt + recent context
  messages = trimToFit(messages, inputBudget);
}
```

## Instructions

### Conversation Trimming
```typescript
function trimConversation(messages: MessageParam[], maxTokens: number): MessageParam[] {
  // Always keep the first message (often contains key context)
  // Keep the most recent messages
  // Drop middle turns first
  if (messages.length <= 4) return messages;

  const first = messages[0];
  const recent = messages.slice(-6); // Last 3 turns
  return [first, ...recent];
}
```

## PII Handling
```typescript
// Strip PII before sending to Claude (if not needed for the task)
function redactPII(text: string): string {
  return text
    .replace(/\b[\w._%+-]+@[\w.-]+\.\w{2,}\b/g, '[EMAIL]')
    .replace(/\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, '[PHONE]')
    .replace(/\b\d{3}-\d{2}-\d{4}\b/g, '[SSN]')
    .replace(/\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, '[CARD]');
}
```

## Data Retention
- **Default**: Anthropic does not use API data for training
- **Zero retention**: Available on Enterprise plans
- **Your responsibility**: Don't store Claude responses containing user PII longer than needed

## Output
- Successful operation confirmed
- Results logged to console

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| API Error | Check error type and status code | See `anthropic-common-errors` |

## Examples
See code blocks above for complete examples.

## Resources
- [Anthropic Privacy Policy](https://www.anthropic.com/policies/privacy)
- [Token Counting](https://docs.anthropic.com/en/api/counting-tokens)
- [Context Window](https://docs.anthropic.com/en/docs/about-claude/models)

## Next Steps
See `anthropic-enterprise-rbac` for organization and access management.

## Prerequisites
- Completed `anthropic-data-install-auth` setup
- Valid API credentials configured
