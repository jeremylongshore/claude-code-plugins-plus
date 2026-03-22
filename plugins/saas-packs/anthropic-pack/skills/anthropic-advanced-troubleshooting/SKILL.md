---
name: anthropic-advanced-troubleshooting
description: |
  Debug complex Claude issues — inconsistent outputs, tool use failures,
  streaming problems, and edge cases.
  Trigger with "claude inconsistent", "anthropic advanced debug",
  "claude tool use broken", "anthropic streaming issues".
allowed-tools: Read, Write, Edit, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, debugging, advanced]
---

# Anthropic Advanced Troubleshooting

## Overview
Core functionality and patterns for anthropic-advanced-troubleshooting.


## Inconsistent Outputs
**Symptom:** Same prompt gives different answers each time.
**Cause:** `temperature` defaults to 1.0 (maximum randomness).
```typescript
// Fix: Set temperature to 0 for deterministic outputs
const message = await client.messages.create({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  temperature: 0, // Deterministic
  messages,
});
```

## Tool Use Failures
**Symptom:** Claude calls a tool that doesn't exist or sends wrong parameters.
```typescript
// Always validate tool calls before executing
const toolUse = response.content.find(b => b.type === 'tool_use');
if (toolUse) {
  const validTools = tools.map(t => t.name);
  if (!validTools.includes(toolUse.name)) {
    console.error(`Claude requested unknown tool: ${toolUse.name}`);
    // Send error back as tool_result
    messages.push({ role: 'assistant', content: response.content });
    messages.push({ role: 'user', content: [{
      type: 'tool_result',
      tool_use_id: toolUse.id,
      is_error: true,
      content: `Tool "${toolUse.name}" does not exist. Available: ${validTools.join(', ')}`,
    }]});
  }
}
```

## Streaming Connection Drops
**Symptom:** Stream stops mid-response without `message_stop` event.
```typescript
// Detect incomplete streams
const stream = client.messages.stream({ ... });
let gotStop = false;

for await (const event of stream) {
  if (event.type === 'message_stop') gotStop = true;
  // ... process events
}

if (!gotStop) {
  console.error('Stream ended without message_stop — connection dropped');
  // Retry the request
}
```

## `max_tokens` Truncation
**Symptom:** Response cuts off mid-sentence.
```typescript
const message = await client.messages.create({ ... });

if (message.stop_reason === 'max_tokens') {
  console.warn('Response truncated — increase max_tokens or ask for shorter output');
  // Option 1: Increase max_tokens
  // Option 2: Add "Be concise" to system prompt
  // Option 3: Continue the response with another call
}
```

## Image/Vision Issues
**Symptom:** Claude says it can't see the image.
- Max image size: 5MB
- Supported: PNG, JPEG, GIF, WebP
- Max 20 images per request
- Base64 encoding must be correct (no data URI prefix in the `data` field)

```typescript
// Correct image format
{
  type: 'image',
  source: {
    type: 'base64',
    media_type: 'image/png', // Must match actual format
    data: buffer.toString('base64'), // Raw base64, no "data:image/png;base64," prefix
  },
}
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
- [Error Types](https://docs.anthropic.com/en/api/errors)
- [Tool Use Guide](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Vision Docs](https://docs.anthropic.com/en/docs/build-with-claude/vision)

## Next Steps
See `anthropic-debug-bundle` for collecting support evidence.

## Prerequisites
- Completed `anthropic-advanced-install-auth` setup
- Valid API credentials configured

## Instructions
Follow the steps in the sections above.
