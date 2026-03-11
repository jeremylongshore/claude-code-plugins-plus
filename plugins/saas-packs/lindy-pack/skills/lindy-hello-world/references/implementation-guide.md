# Lindy Hello World - Implementation Guide

# Lindy Hello World

## Overview
Minimal working example demonstrating core Lindy AI agent functionality.

## Prerequisites
- Completed `lindy-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { Lindy } from '@lindy-ai/sdk';

const lindy = new Lindy({
  apiKey: process.env.LINDY_API_KEY,
});
```

### Step 3: Create Your First Agent
```typescript
async function main() {
  // Create a simple AI agent
  const agent = await lindy.agents.create({
    name: 'Hello World Agent',
    description: 'My first Lindy agent',
    instructions: 'You are a helpful assistant that greets users.',
  });

  console.log(`Created agent: ${agent.id}`);

  // Run the agent with a simple task
  const result = await lindy.agents.run(agent.id, {
    input: 'Say hello to the world!',
  });

  console.log(`Agent response: ${result.output}`);
}

main().catch(console.error);
```

## Output
- Working code file with Lindy client initialization
- Created AI agent in your Lindy workspace
- Console output showing:
```
Created agent: agt_abc123
Agent response: Hello, World! I'm your new Lindy AI assistant.
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list @lindy-ai/sdk` |
| Auth Error | Invalid credentials | Check environment variable is set |
| Timeout | Network issues | Increase timeout or check connectivity |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |

## Examples

### TypeScript Example
```typescript
import { Lindy } from '@lindy-ai/sdk';

const lindy = new Lindy({
  apiKey: process.env.LINDY_API_KEY,
});

async function main() {
  const agent = await lindy.agents.create({
    name: 'Greeting Agent',
    instructions: 'Greet users warmly and helpfully.',
  });

  const result = await lindy.agents.run(agent.id, {
    input: 'Hello!',
  });

  console.log(result.output);
}

main().catch(console.error);
```

### Python Example
```python
from lindy import Lindy

client = Lindy()

agent = client.agents.create(
    name="Greeting Agent",
    instructions="Greet users warmly and helpfully."
)

result = client.agents.run(agent.id, input="Hello!")
print(result.output)
```

## Resources
- [Lindy Getting Started](https://docs.lindy.ai/getting-started)
- [Lindy API Reference](https://docs.lindy.ai/api)
- [Lindy Examples](https://docs.lindy.ai/examples)

## Next Steps
Proceed to `lindy-local-dev-loop` for development workflow setup.
