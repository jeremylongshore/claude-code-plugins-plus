# Lindy Local Dev Loop - Implementation Guide

# Lindy Local Dev Loop

## Overview
Configure efficient local development workflow for Lindy AI agent development.

## Prerequisites
- Completed `lindy-install-auth` setup
- Node.js 18+ with npm/pnpm
- Code editor with TypeScript support

## Instructions

### Step 1: Set Up Project Structure
```bash
mkdir lindy-agents && cd lindy-agents
npm init -y
npm install @lindy-ai/sdk typescript ts-node dotenv
npm install -D @types/node nodemon
```

### Step 2: Configure TypeScript
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["src/**/*"]
}
```

### Step 3: Create Development Script
```json
// package.json scripts
{
  "scripts": {
    "dev": "nodemon --exec ts-node src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test:agent": "ts-node src/test-agent.ts"
  }
}
```

### Step 4: Create Agent Test Harness
```typescript
// src/test-agent.ts
import 'dotenv/config';
import { Lindy } from '@lindy-ai/sdk';

const lindy = new Lindy({ apiKey: process.env.LINDY_API_KEY });

async function testAgent(agentId: string, input: string) {
  console.log(`Testing agent ${agentId} with: "${input}"`);
  const start = Date.now();

  const result = await lindy.agents.run(agentId, { input });

  console.log(`Response (${Date.now() - start}ms): ${result.output}`);
  return result;
}

// Run test
testAgent(process.argv[2], process.argv[3] || 'Hello!');
```

## Output
- Configured development environment
- Hot reload enabled for agent code
- Test harness for rapid iteration
- TypeScript support with type checking

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| ts-node not found | Dev deps missing | `npm install -D ts-node` |
| ENV not loaded | dotenv not configured | Add `import 'dotenv/config'` |
| Type errors | Missing types | `npm install -D @types/node` |

## Examples

### Watch Mode Development
```bash
# Start development with hot reload
npm run dev

# Test specific agent
npm run test:agent agt_abc123 "Test input"
```

### Environment Setup
```bash
# .env file
LINDY_API_KEY=your-api-key
LINDY_ENVIRONMENT=development
```

## Resources
- [Lindy SDK Reference](https://docs.lindy.ai/sdk)
- [TypeScript Best Practices](https://docs.lindy.ai/typescript)

## Next Steps
Proceed to `lindy-sdk-patterns` for SDK best practices.
