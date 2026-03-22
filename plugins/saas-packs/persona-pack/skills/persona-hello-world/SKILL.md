---
name: persona-hello-world
description: |
  Create a minimal working Persona example.
  Use when starting a new Persona integration, testing your setup,
  or learning basic Persona API patterns.
  Trigger with phrases like "persona hello world", "persona example",
  "persona quick start", "simple persona code".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, persona]
---

# Persona Hello World

## Overview
Minimal working example demonstrating core Persona functionality.

## Prerequisites
- Completed `persona-install-auth` setup
- Valid API credentials configured
- Development environment ready

## Instructions

### Step 1: Create Entry File
Create a new file for your hello world example.

### Step 2: Import and Initialize Client
```typescript
import { PersonaClient } from '@persona/sdk';

const client = new PersonaClient({
  apiKey: process.env.PERSONA_API_KEY,
});
```

### Step 3: Make Your First API Call
```typescript
async function main() {
  // Your first API call here
}

main().catch(console.error);
```

## Output
- Working code file with Persona client initialization
- Successful API response confirming connection
- Console output showing:
```
Success! Your Persona connection is working.
```

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | SDK not installed | Verify with `npm list` or `pip show` |
| Auth Error | Invalid credentials | Check environment variable is set |
| Timeout | Network issues | Increase timeout or check connectivity |
| Rate Limit | Too many requests | Wait and retry with exponential backoff |

## Examples

### TypeScript Example
```typescript
import { PersonaClient } from '@persona/sdk';

const client = new PersonaClient({
  apiKey: process.env.PERSONA_API_KEY,
});

async function main() {
  // Your first API call here
}

main().catch(console.error);
```

### Python Example
```python
from persona import PersonaClient

client = PersonaClient()

# Your first API call here
```

## Resources
- [Persona Getting Started](https://docs.persona.com/getting-started)
- [Persona API Reference](https://docs.persona.com/api)
- [Persona Examples](https://docs.persona.com/examples)

## Next Steps
Proceed to `persona-local-dev-loop` for development workflow setup.