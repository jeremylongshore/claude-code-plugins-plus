---
name: langfuse-hello-world
description: |
  Create a minimal working Langfuse trace example.
  Use when starting a new Langfuse integration, testing your setup,
  or learning basic Langfuse tracing patterns.
  Trigger with phrases like "langfuse hello world", "langfuse example",
  "langfuse quick start", "first langfuse trace", "simple langfuse code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Hello World

## Overview
Minimal working example demonstrating core Langfuse tracing functionality.

## Prerequisites
- Completed `langfuse-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File

Create a new file for your hello world trace.

### Step 2: Import and Initialize Client

```typescript
import { Langfuse } from "langfuse";

const langfuse = new Langfuse({
  publicKey: process.env.LANGFUSE_PUBLIC_KEY!,
  secretKey: process.env.LANGFUSE_SECRET_KEY!,
  baseUrl: process.env.LANGFUSE_HOST,
});
```

### Step 3: Create Your First Trace

```typescript
async function helloLangfuse() {
  // Create a trace (top-level operation)
  const trace = langfuse.trace({
    name: "hello-world",
    userId: "demo-user",
    metadata: { source: "hello-world-example" },
    tags: ["demo", "getting-started"],
  });

  // Add a span (child operation)
  const span = trace.span({
    name: "process-input",
    input: { message: "Hello, Langfuse!" },
  });

  // Simulate some processing
  await new Promise((resolve) => setTimeout(resolve, 100));

  // End the span with output
  span.end({
    output: { result: "Processed successfully!" },
  });

  // Add a generation (LLM call tracking)
  trace.generation({
    name: "llm-response",
    model: "gpt-4",
    input: [{ role: "user", content: "Say hello" }],
    output: { content: "Hello! How can I help you today?" },
    usage: {
      promptTokens: 5,
      completionTokens: 10,
      totalTokens: 15,
    },
  });

  // Flush to ensure data is sent
  await langfuse.flushAsync();

  console.log("Trace created! View at:", trace.getTraceUrl());
}

helloLangfuse().catch(console.error);
```

## Output
- Working code file with Langfuse client initialization
- A trace visible in Langfuse dashboard containing:
  - One span with input/output
  - One generation with mock LLM data
- Console output showing:
```
Trace created! View at: https://cloud.langfuse.com/trace/abc123...
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list langfuse` |
| Auth Error | Invalid credentials | Check environment variables are set |
| Trace not appearing | Data not flushed | Ensure `flushAsync()` is called |
| Network Error | Host unreachable | Verify LANGFUSE_HOST URL |

## Examples

### TypeScript Complete Example
```typescript
import { Langfuse } from "langfuse";

const langfuse = new Langfuse();

async function main() {
  // Create trace
  const trace = langfuse.trace({
    name: "hello-world",
    input: { query: "What is Langfuse?" },
  });

  // Simulate LLM call
  const generation = trace.generation({
    name: "answer-query",
    model: "gpt-4",
    modelParameters: { temperature: 0.7 },
    input: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: "What is Langfuse?" },
    ],
  });

  // Simulate response
  await new Promise((r) => setTimeout(r, 500));  # HTTP 500 Internal Server Error

  // End generation with output
  generation.end({
    output: "Langfuse is an open-source LLM observability platform...",
    usage: { promptTokens: 25, completionTokens: 50 },
  });

  // Update trace with final output
  trace.update({
    output: { answer: "Langfuse is an LLM observability platform." },
  });

  // Flush and get URL
  await langfuse.flushAsync();
  console.log("View trace:", trace.getTraceUrl());
}

main();
```

### Python Complete Example
```python
from langfuse import Langfuse
import time

langfuse = Langfuse()

def main():
    # Create trace
    trace = langfuse.trace(
        name="hello-world",
        input={"query": "What is Langfuse?"},
        user_id="demo-user",
    )

    # Add a span for processing
    span = trace.span(
        name="process-query",
        input={"query": "What is Langfuse?"},
    )

    # Simulate processing
    time.sleep(0.1)

    span.end(output={"processed": True})

    # Add LLM generation
    generation = trace.generation(
        name="answer-query",
        model="gpt-4",
        model_parameters={"temperature": 0.7},
        input=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is Langfuse?"},
        ],
    )

    # Simulate LLM response
    time.sleep(0.5)

    generation.end(
        output="Langfuse is an open-source LLM observability platform...",
        usage={"prompt_tokens": 25, "completion_tokens": 50},
    )

    # Update trace with final output
    trace.update(
        output={"answer": "Langfuse is an LLM observability platform."}
    )

    # Flush data
    langfuse.flush()
    print(f"View trace: {trace.get_trace_url()}")

if __name__ == "__main__":
    main()
```

### With Decorators (Python)
```python
from langfuse.decorators import observe, langfuse_context

@observe()
def process_query(query: str) -> str:
    # This function is automatically traced
    return f"Processed: {query}"

@observe(as_type="generation")
def generate_response(messages: list) -> str:
    # This is tracked as an LLM generation
    langfuse_context.update_current_observation(
        model="gpt-4",
        usage={"prompt_tokens": 10, "completion_tokens": 20},
    )
    return "Hello from Langfuse!"

@observe()
def main():
    result = process_query("Hello!")
    response = generate_response([{"role": "user", "content": "Hi"}])
    return response

main()
```

## Resources
- [Langfuse Tracing Concepts](https://langfuse.com/docs/tracing)
- [Langfuse SDK Reference](https://langfuse.com/docs/sdk)
- [Langfuse Examples](https://langfuse.com/docs/get-started)

## Next Steps
Proceed to `langfuse-local-dev-loop` for development workflow setup.