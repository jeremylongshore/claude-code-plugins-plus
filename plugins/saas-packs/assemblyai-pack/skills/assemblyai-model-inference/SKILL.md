---
name: assemblyai-model-inference
description: |
  Execute AssemblyAI primary workflow: Model Inference Pipeline.
  Use when sending chat completions with system prompts,
  streaming responses for real-time UX, or batch processing documents through the model.
  Trigger with phrases like "assemblyai inference",
  "run model inference with assemblyai".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, assemblyai]
---

# AssemblyAI Model Inference Pipeline

## Overview
Send prompts to the model API and process streaming or batch responses.
This is the core money-path — every integration starts here.


## Prerequisites
- Completed `assemblyai-install-auth` setup

- Understanding of model IDs, token limits, and streaming patterns

- Valid API credentials configured

## Instructions

### Step 1: Configure Model Parameters
```typescript
const config = {
  model: process.env.MODEL_ID || 'default',
  temperature: 0.7,
  max_tokens: 2048,
  stream: true,
};

```

### Step 2: Send Completion Request
```typescript
const stream = await client.chat.completions.create({
  ...config,
  messages: [
    { role: 'system', content: 'You are a helpful assistant.' },
    { role: 'user', content: userInput },
  ],
});
for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '');
}

```

### Step 3: Handle Response and Token Usage
```typescript
// For non-streaming responses:
const usage = response.usage;
console.log(`Tokens: ${usage.prompt_tokens} in / ${usage.completion_tokens} out`);
console.log(`Cost estimate: $${((usage.prompt_tokens * 0.003 + usage.completion_tokens * 0.015) / 1000).toFixed(4)}`);

```

## Output
- Completed Model Inference Pipeline execution

- Model response with token usage and cost estimate
- Streaming or batch completion depending on configuration

- Success confirmation or error details

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Context Length Exceeded | Input + max_tokens exceeds model context window | Truncate input or reduce max_tokens. Check model's context limit. |
| Model Not Found | Invalid model ID or model not available on your plan | Call /models endpoint to list available models. Check plan access. |

## Examples

### Complete Workflow
```typescript
import { Client } from 'vendor-sdk';
const client = new Client({ apiKey: process.env.API_KEY });

async function inference(prompt: string) {
  const response = await client.chat.completions.create({
    model: 'default',
    messages: [{ role: 'user', content: prompt }],
    max_tokens: 1024,
  });
  return response.choices[0].message.content;
}

```

### Common Variations
- **Streaming**: Set `stream: true` for real-time token delivery
- **JSON mode**: Set `response_format: { type: 'json_object' }` for structured output
- **Multi-turn**: Append assistant responses to messages array for conversation


## Resources
- [AssemblyAI Documentation](https://docs.assemblyai.com)
- [AssemblyAI API Reference](https://docs.assemblyai.com/api)

## Next Steps
For secondary workflow, see `assemblyai-embeddings-search`.