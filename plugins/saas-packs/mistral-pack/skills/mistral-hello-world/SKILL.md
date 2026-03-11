---
name: mistral-hello-world
description: |
  Create a minimal working Mistral AI chat completion example.
  Use when starting a new Mistral integration, testing your setup,
  or learning basic Mistral API patterns.
  Trigger with phrases like "mistral hello world", "mistral example",
  "mistral quick start", "simple mistral code", "mistral chat".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Hello World

## Overview
Minimal working example demonstrating core Mistral AI chat completion functionality.

## Prerequisites
- Completed `mistral-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File

**TypeScript (hello-mistral.ts)**
```typescript
import Mistral from '@mistralai/mistralai';

const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
});

async function main() {
  const response = await client.chat.complete({
    model: 'mistral-small-latest',
    messages: [
      { role: 'user', content: 'Say "Hello, World!" in a creative way.' }
    ],
  });

  console.log(response.choices?.[0]?.message?.content);
}

main().catch(console.error);
```

**Python (hello_mistral.py)**
```python
import os
from mistralai import Mistral

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

def main():
    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[
            {"role": "user", "content": "Say 'Hello, World!' in a creative way."}
        ],
    )

    print(response.choices[0].message.content)

if __name__ == "__main__":
    main()
```

### Step 2: Run the Example

```bash
# TypeScript
npx tsx hello-mistral.ts

# Python
python hello_mistral.py
```

### Step 3: Streaming Response (Advanced)

**TypeScript Streaming**
```typescript
import Mistral from '@mistralai/mistralai';

const client = new Mistral({
  apiKey: process.env.MISTRAL_API_KEY,
});

async function streamChat() {
  const stream = await client.chat.stream({
    model: 'mistral-small-latest',
    messages: [
      { role: 'user', content: 'Tell me a short story about AI.' }
    ],
  });

  for await (const event of stream) {
    const content = event.data?.choices?.[0]?.delta?.content;
    if (content) {
      process.stdout.write(content);
    }
  }
  console.log(); // newline
}

streamChat().catch(console.error);
```

**Python Streaming**
```python
import os
from mistralai import Mistral

client = Mistral(api_key=os.environ.get("MISTRAL_API_KEY"))

def stream_chat():
    stream = client.chat.stream(
        model="mistral-small-latest",
        messages=[
            {"role": "user", "content": "Tell me a short story about AI."}
        ],
    )

    for event in stream:
        content = event.data.choices[0].delta.content
        if content:
            print(content, end="", flush=True)
    print()  # newline

if __name__ == "__main__":
    stream_chat()
```

## Output
- Working code file with Mistral client initialization
- Successful API response with generated text
- Console output showing:
```
Hello, World!

(But spoken by a million synchronized starlings,
spelling it across the twilight sky...)
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list @mistralai/mistralai` |
| Auth Error | Invalid credentials | Check MISTRAL_API_KEY is set |
| Timeout | Network issues | Increase timeout or check connectivity |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |

## Examples

### Multi-turn Conversation
```typescript
const messages = [
  { role: 'system', content: 'You are a helpful assistant.' },
  { role: 'user', content: 'What is the capital of France?' },
];

const response1 = await client.chat.complete({
  model: 'mistral-small-latest',
  messages,
});

// Add assistant response to conversation
messages.push({
  role: 'assistant',
  content: response1.choices?.[0]?.message?.content || '',
});

// Continue conversation
messages.push({ role: 'user', content: 'What about Germany?' });

const response2 = await client.chat.complete({
  model: 'mistral-small-latest',
  messages,
});

console.log(response2.choices?.[0]?.message?.content);
```

### With Temperature Control
```typescript
const response = await client.chat.complete({
  model: 'mistral-small-latest',
  messages: [{ role: 'user', content: 'Write a haiku about coding.' }],
  temperature: 0.7, // 0-1, higher = more creative
  maxTokens: 100,
});
```

## Resources
- [Mistral AI Chat Completions](https://docs.mistral.ai/api/#tag/chat)
- [Mistral AI Models](https://docs.mistral.ai/getting-started/models/)
- [Mistral AI Streaming](https://docs.mistral.ai/capabilities/completion/#streaming)

## Next Steps
Proceed to `mistral-local-dev-loop` for development workflow setup.