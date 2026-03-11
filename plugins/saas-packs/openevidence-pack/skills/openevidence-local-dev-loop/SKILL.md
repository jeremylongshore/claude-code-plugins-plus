---
name: openevidence-local-dev-loop
description: |
  Set up local development environment for OpenEvidence integration.
  Use when configuring development workflow, setting up testing environment,
  or creating a rapid iteration loop for clinical AI development.
  Trigger with phrases like "openevidence dev setup", "openevidence local",
  "openevidence development", "openevidence testing environment".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Local Dev Loop

## Overview
Set up a rapid development loop for building and testing OpenEvidence integrations locally.

## Prerequisites
- Completed `openevidence-install-auth` setup
- Node.js 18+ with npm/pnpm or Python 3.10+
- Text editor or IDE configured
- Git repository initialized

## Instructions

### Step 1: Project Structure
```bash
mkdir -p src/{openevidence,services,utils}
mkdir -p tests/{unit,integration}
mkdir -p config

# Create essential files
touch src/openevidence/{client,types,errors}.ts
touch src/services/clinical-query.ts
touch tests/integration/openevidence.test.ts
touch config/{development,test}.json
```

### Step 2: Environment Configuration
```bash
# .env.development
cat > .env.development << 'EOF'
OPENEVIDENCE_API_KEY=oe_sandbox_***
OPENEVIDENCE_ORG_ID=org_sandbox_***
OPENEVIDENCE_BASE_URL=https://api.sandbox.openevidence.com
OPENEVIDENCE_TIMEOUT=60000  # 60000: 1 minute in ms
LOG_LEVEL=debug
EOF

# .env.test
cat > .env.test << 'EOF'
OPENEVIDENCE_API_KEY=oe_test_***
OPENEVIDENCE_ORG_ID=org_test_***
OPENEVIDENCE_BASE_URL=https://api.sandbox.openevidence.com
OPENEVIDENCE_TIMEOUT=30000  # 30000: 30 seconds in ms
LOG_LEVEL=error
EOF
```

### Step 3: Dev Dependencies
```bash
set -euo pipefail
# TypeScript project
npm install -D typescript ts-node vitest @types/node dotenv-cli

# Add scripts to package.json
npm pkg set scripts.dev="dotenv -e .env.development -- ts-node src/index.ts"
npm pkg set scripts.test="dotenv -e .env.test -- vitest"
npm pkg set scripts.test:integration="dotenv -e .env.test -- vitest run tests/integration"
npm pkg set scripts.watch="ts-node-dev --respawn src/index.ts"
```

### Step 4: Development Client Wrapper
```typescript
// src/openevidence/client.ts
import { OpenEvidenceClient } from '@openevidence/sdk';

interface ClientConfig {
  apiKey: string;
  orgId: string;
  baseUrl?: string;
  timeout?: number;
}

let clientInstance: OpenEvidenceClient | null = null;

export function getClient(config?: Partial<ClientConfig>): OpenEvidenceClient {
  if (!clientInstance || config) {
    clientInstance = new OpenEvidenceClient({
      apiKey: config?.apiKey || process.env.OPENEVIDENCE_API_KEY!,
      orgId: config?.orgId || process.env.OPENEVIDENCE_ORG_ID!,
      baseUrl: config?.baseUrl || process.env.OPENEVIDENCE_BASE_URL,
      timeout: config?.timeout || parseInt(process.env.OPENEVIDENCE_TIMEOUT || '30000'),  # 30000: 30 seconds in ms
    });
  }
  return clientInstance;
}

// For testing - allows resetting singleton
export function resetClient(): void {
  clientInstance = null;
}
```

### Step 5: Mock Client for Unit Tests
```typescript
// tests/mocks/openevidence.ts
import { vi } from 'vitest';

export const mockClinicalQuery = vi.fn().mockResolvedValue({
  answer: 'Mock clinical answer for testing',
  citations: [
    { source: 'Test Journal 2025', title: 'Test Article', authors: ['Test Author'] }  # 2025 year
  ],
  confidence: 0.95,
  lastUpdated: '2025-01-01',
});

export const mockOpenEvidenceClient = {
  query: mockClinicalQuery,
  deepConsult: vi.fn(),
  health: { check: vi.fn().mockResolvedValue({ status: 'healthy' }) },
};

vi.mock('@openevidence/sdk', () => ({
  OpenEvidenceClient: vi.fn(() => mockOpenEvidenceClient),
}));
```

### Step 6: Hot Reload Development Script
```typescript
// scripts/dev-server.ts
import { watch } from 'chokidar';
import { spawn, ChildProcess } from 'child_process';

let serverProcess: ChildProcess | null = null;

function startServer() {
  if (serverProcess) {
    serverProcess.kill();
  }

  console.log('[dev] Starting server...');
  serverProcess = spawn('npx', ['ts-node', 'src/index.ts'], {
    stdio: 'inherit',
    env: { ...process.env, NODE_ENV: 'development' },
  });
}

// Watch for changes
watch('src/**/*.ts', { ignoreInitial: false })
  .on('all', (event, path) => {
    console.log(`[dev] ${event}: ${path}`);
    startServer();
  });
```

## Output
- Configured development environment with hot reload
- Separate environment files for dev/test
- Mock client for unit testing
- Integration test setup for sandbox API

## Development Workflow
```bash
set -euo pipefail
# Start development with hot reload
npm run dev

# Run unit tests in watch mode
npm test

# Run integration tests against sandbox
npm run test:integration

# Type check
npx tsc --noEmit
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Env vars undefined | .env not loaded | Check dotenv-cli is running |
| Sandbox unavailable | Wrong base URL | Verify OPENEVIDENCE_BASE_URL |
| Tests timing out | Network issues | Mock client for unit tests |
| Hot reload not working | File watcher issue | Restart dev script |

## Examples

### Integration Test Example
```typescript
// tests/integration/openevidence.test.ts
import { describe, it, expect, beforeAll } from 'vitest';
import { getClient, resetClient } from '../../src/openevidence/client';

describe('OpenEvidence Integration', () => {
  beforeAll(() => {
    resetClient();
  });

  it('should successfully query clinical evidence', async () => {
    const client = getClient();

    const response = await client.query({
      question: 'What is the half-life of aspirin?',
      context: { specialty: 'pharmacology' },
    });

    expect(response.answer).toBeDefined();
    expect(response.citations.length).toBeGreaterThan(0);
    expect(response.confidence).toBeGreaterThan(0.5);
  }, 30000); // 30s timeout for API calls  # 30000: 30 seconds in ms
});
```

### Unit Test with Mocks
```typescript
// tests/unit/clinical-query.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mockClinicalQuery, mockOpenEvidenceClient } from '../mocks/openevidence';
import { queryClinicalEvidence } from '../../src/services/clinical-query';

describe('Clinical Query Service', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return formatted clinical answer', async () => {
    const result = await queryClinicalEvidence('test question');

    expect(mockClinicalQuery).toHaveBeenCalledWith(
      expect.objectContaining({ question: 'test question' })
    );
    expect(result.answer).toBe('Mock clinical answer for testing');
  });
});
```

## Resources
- [OpenEvidence Sandbox](https://sandbox.openevidence.com/)
- [Vitest Documentation](https://vitest.dev/)
- [ts-node-dev](https://github.com/wclr/ts-node-dev)

## Next Steps
For SDK patterns and best practices, see `openevidence-sdk-patterns`.