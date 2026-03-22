---
name: anthropic-core-workflow-a
description: |
  Redirect to anthropic-model-inference for Messages API streaming,
  vision, and structured output patterns.
  Use when looking for the primary Anthropic workflow.
  Trigger with "anthropic workflow", "claude main workflow".
allowed-tools: Read
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude]
---

# Anthropic Core Workflow A → Model Inference

## Overview
This skill redirects to `anthropic-model-inference` which covers streaming, vision, structured output, and all Messages API patterns.

## Prerequisites
- Completed `anthropic-install-auth` setup
- `ANTHROPIC_API_KEY` configured

## Instructions

### Step 1: Use anthropic-model-inference instead
This skill has been replaced. The primary Anthropic workflow is the Messages API, covered in full by `anthropic-model-inference`.

### Step 2: Key topics covered there
- Streaming responses with `client.messages.stream()`
- Vision — sending images to Claude
- Structured JSON output via system prompts
- Multi-turn conversations
- All Messages API parameters

## Output
- Redirected to `anthropic-model-inference`
- All Messages API patterns available there

## Error Handling
| Issue | Solution |
|-------|----------|
| Skill not found | Run `anthropic-model-inference` directly |

## Examples
```typescript
// Use anthropic-model-inference for the full Messages API guide
import Anthropic from '@anthropic-ai/sdk';
const client = new Anthropic();
const stream = client.messages.stream({
  model: 'claude-sonnet-4-20250514',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Hello!' }],
});
```

## Resources
- [Messages API](https://docs.anthropic.com/en/api/messages)
- [Streaming](https://docs.anthropic.com/en/api/messages-streaming)

## Next Steps
Run `anthropic-model-inference` for the complete guide.
