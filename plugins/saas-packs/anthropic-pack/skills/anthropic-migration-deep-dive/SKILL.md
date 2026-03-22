---
name: anthropic-migration-deep-dive
description: |
  Migrate from OpenAI/GPT to Anthropic/Claude — API differences,
  prompt adaptation, SDK swap, and feature mapping.
  Trigger with "migrate to claude", "openai to anthropic",
  "switch from gpt to claude", "replace openai with anthropic".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, migration, openai]
---

# Migrate from OpenAI to Anthropic

## Overview
Core functionality and patterns for anthropic-migration-deep-dive.


## API Mapping

| OpenAI | Anthropic | Notes |
|--------|-----------|-------|
| `openai.chat.completions.create()` | `anthropic.messages.create()` | Different request/response shape |
| `model: 'gpt-4o'` | `model: 'claude-sonnet-4-20250514'` | Different model IDs |
| `response.choices[0].message.content` | `response.content[0].text` | Different response path |
| `system` in messages array | `system` as separate parameter | Claude uses top-level `system` |
| `response_format: { type: 'json_object' }` | System prompt: "Respond in JSON only" | No native JSON mode |
| `tools` / `function_calling` | `tools` (similar but different schema) | Input schema differences |
| `openai.embeddings.create()` | N/A — use Voyage or Cohere | No embeddings API |

## SDK Swap

## Instructions

### Before (OpenAI)
```typescript
import OpenAI from 'openai';
const openai = new OpenAI();

const response = await openai.chat.completions.create({
  model: 'gpt-4o',
  messages: [
    { role: 'system', content: 'You are helpful.' },
    { role: 'user', content: 'Hello' },
  ],
});
console.log(response.choices[0].message.content);
```

### After (Anthropic)
```typescript
import Anthropic from '@anthropic-ai/sdk';
const anthropic = new Anthropic();

const response = await anthropic.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024, // Required (not optional like OpenAI)
  system: 'You are helpful.', // Separate from messages
  messages: [
    { role: 'user', content: 'Hello' },
  ],
});
console.log(response.content[0].text);
```

## Key Differences
1. **`max_tokens` is required** — OpenAI defaults it, Anthropic requires it
2. **`system` is a top-level param** — not a message in the array
3. **First message must be `user`** — can't start with assistant
4. **Messages must alternate** — no two user or two assistant messages in a row
5. **Response shape** — `content[0].text` not `choices[0].message.content`
6. **Streaming events** — different event types and structure

## Tool Use Migration
```typescript
// OpenAI tool definition
{ type: 'function', function: { name: 'get_weather', parameters: { ... } } }

// Anthropic tool definition
{ name: 'get_weather', input_schema: { ... } }  // Flatter structure
```

## Grep & Replace
```bash
# Find all OpenAI imports
grep -rn "from 'openai'" --include="*.ts" .
grep -rn "import OpenAI" --include="*.ts" .

# Find response access patterns to update
grep -rn "choices\[0\]" --include="*.ts" .
grep -rn "message.content" --include="*.ts" .  # May need updating
```

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
- [Anthropic Messages API](https://docs.anthropic.com/en/api/messages)
- [Migration Guide](https://docs.anthropic.com/en/docs/about-claude/models)

## Next Steps
See `anthropic-sdk-patterns` for production Anthropic SDK patterns.

## Prerequisites
- Completed `anthropic-migration-deep-install-auth` setup
- Valid API credentials configured
