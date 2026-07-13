# MaintainX Local Dev Loop - Implementation Guide

> Full implementation details and code examples for the `maintainx-local-dev-loop` skill.

# MaintainX Local Dev Loop

## Overview

Set up an efficient local development workflow for building and testing MaintainX integrations.

## Prerequisites

- Completed `maintainx-install-auth` setup
- Node.js 18+ installed
- Docker (optional, for local testing)
- VS Code or preferred IDE

## Instructions

### Step 1: Project Structure

```bash
# Create project structure
mkdir -p maintainx-integration/{src/{api,models,utils},tests,scripts}
cd maintainx-integration

# Initialize project
npm init -y
npm install axios dotenv typescript ts-node @types/node
npm install -D jest @types/jest ts-jest nodemon
```

```
maintainx-integration/
├── src/
│   ├── api/
│   │   └── client.ts         # MaintainX API client
│   ├── models/
│   │   ├── work-order.ts     # Work order types
│   │   ├── asset.ts          # Asset types
│   │   └── location.ts       # Location types
│   ├── utils/
│   │   ├── pagination.ts     # Cursor pagination helper
│   │   └── retry.ts          # Retry logic
│   └── index.ts              # Main entry point
├── tests/
│   ├── api.test.ts           # API integration tests
│   └── mocks/                # Mock responses
├── scripts/
│   └── seed-data.ts          # Seed test data
├── .env.development          # Dev environment vars
├── .env.test                 # Test environment vars
├── tsconfig.json
├── jest.config.js
└── package.json
```

### Step 2: Environment Configuration

```bash
# .env.development
MAINTAINX_API_KEY=your-dev-api-key
MAINTAINX_BASE_URL=https://api.getmaintainx.com/v1
LOG_LEVEL=debug
NODE_ENV=development
```

```bash
# .env.test
MAINTAINX_API_KEY=your-test-api-key
MAINTAINX_BASE_URL=https://api.getmaintainx.com/v1
LOG_LEVEL=error
NODE_ENV=test
```

```typescript
// src/config.ts
import dotenv from 'dotenv';
import path from 'path';

const envFile = process.env.NODE_ENV === 'test'
  ? '.env.test'
  : '.env.development';

dotenv.config({ path: path.resolve(process.cwd(), envFile) });

export const config = {
  maintainx: {
    apiKey: process.env.MAINTAINX_API_KEY!,
    baseUrl: process.env.MAINTAINX_BASE_URL || 'https://api.getmaintainx.com/v1',
  },
  logLevel: process.env.LOG_LEVEL || 'info',
  isDevelopment: process.env.NODE_ENV === 'development',
  isTest: process.env.NODE_ENV === 'test',
};
```

### Step 3: TypeScript Configuration

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "lib": ["ES2022"],
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "dist", "tests"]
}
```

### Step 4: Dev Scripts Configuration

```json
// package.json (scripts section)
{
  "scripts": {
    "dev": "nodemon --exec ts-node src/index.ts",
    "build": "tsc",
    "test": "NODE_ENV=test jest",
    "test:watch": "NODE_ENV=test jest --watch",
    "test:integration": "NODE_ENV=test jest --testPathPattern=integration",
    "lint": "eslint src/**/*.ts",
    "seed": "ts-node scripts/seed-data.ts",
    "repl": "ts-node",
    "api:test": "ts-node scripts/api-test.ts"
  }
}
```

### Step 5: Interactive REPL for Testing

```typescript
// scripts/repl.ts
import repl from 'repl';
import { MaintainXClient } from '../src/api/client';

const client = new MaintainXClient();

const r = repl.start('maintainx> ');

// Add client to context
r.context.client = client;
r.context.help = () => {
  console.log(`
Available commands:
  client.getWorkOrders()     - List work orders
  client.getWorkOrder(id)    - Get single work order
  client.createWorkOrder({}) - Create work order
  client.getAssets()         - List assets
  client.getLocations()      - List locations
  client.getUsers()          - List users

Example:
  await client.getWorkOrders({ limit: 5 })
`);
};

console.log('MaintainX REPL started. Type help() for commands.');
```

### Step 6: Mock Server for Offline Development

```typescript
// tests/mocks/server.ts
import express from 'express';

const app = express();
app.use(express.json());

// Mock work orders
const mockWorkOrders = [
  {
    id: 'wo_mock_001',
    title: 'Mock Work Order 1',
    status: 'OPEN',
    priority: 'MEDIUM',
    createdAt: new Date().toISOString(),
  },
  {
    id: 'wo_mock_002',
    title: 'Mock Work Order 2',
    status: 'IN_PROGRESS',
    priority: 'HIGH',
    createdAt: new Date().toISOString(),
  },
];

app.get('/v1/workorders', (req, res) => {
  const limit = parseInt(req.query.limit as string) || 10;
  res.json({
    workOrders: mockWorkOrders.slice(0, limit),
    nextCursor: null,
  });
});

app.get('/v1/workorders/:id', (req, res) => {
  const wo = mockWorkOrders.find(w => w.id === req.params.id);
  if (wo) {
    res.json(wo);
  } else {
    res.status(404).json({ error: 'Work order not found' });
  }
});

app.post('/v1/workorders', (req, res) => {
  const newWo = {
    id: `wo_mock_${Date.now()}`,
    ...req.body,
    status: 'OPEN',
    createdAt: new Date().toISOString(),
  };
  mockWorkOrders.push(newWo);
  res.status(201).json(newWo);
});

// Start server
const PORT = process.env.MOCK_PORT || 3001;
app.listen(PORT, () => {
  console.log(`Mock MaintainX server running on port ${PORT}`);
});

export { app };
```

### Step 7: Nodemon Configuration

```json
// nodemon.json
{
  "watch": ["src"],
  "ext": "ts,json",
  "ignore": ["src/**/*.test.ts"],
  "exec": "ts-node src/index.ts"
}
```

### Step 8: Jest Configuration

```javascript
// jest.config.js
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/tests'],
  testMatch: ['**/*.test.ts'],
  collectCoverageFrom: ['src/**/*.ts'],
  coverageDirectory: 'coverage',
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testTimeout: 10000,
};
```

```typescript
// tests/setup.ts
import dotenv from 'dotenv';
dotenv.config({ path: '.env.test' });

// Global test setup
beforeAll(() => {
  console.log('Test environment initialized');
});

afterAll(() => {
  console.log('Test cleanup complete');
});
```

### Step 9: Sample Integration Test

```typescript
// tests/api.test.ts
import { MaintainXClient } from '../src/api/client';

describe('MaintainX API', () => {
  let client: MaintainXClient;

  beforeAll(() => {
    client = new MaintainXClient();
  });

  describe('Work Orders', () => {
    it('should list work orders', async () => {
      const response = await client.getWorkOrders({ limit: 5 });
      expect(response.data).toHaveProperty('workOrders');
      expect(Array.isArray(response.data.workOrders)).toBe(true);
    });

    it('should create a work order', async () => {
      const response = await client.createWorkOrder({
        title: 'Test Work Order - Jest',
        description: 'Created during automated testing',
        priority: 'LOW',
      });
      expect(response.data).toHaveProperty('id');
      expect(response.data.title).toBe('Test Work Order - Jest');
    });
  });

  describe('Assets', () => {
    it('should list assets', async () => {
      const response = await client.getAssets({ limit: 5 });
      expect(response.data).toHaveProperty('assets');
    });
  });
});
```

## Output

- Fully configured development environment
- TypeScript project with hot reload
- Mock server for offline testing
- Jest test suite configured
- Interactive REPL for exploration

## Workflow Commands

```bash
# Start development with hot reload
npm run dev

# Run tests
npm test

# Watch mode for tests
npm run test:watch

# Interactive REPL
npm run repl

# Seed test data
npm run seed

# Start mock server (separate terminal)
npx ts-node tests/mocks/server.ts
```

## Resources

- [MaintainX API Documentation](https://maintainx.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Jest Documentation](https://jestjs.io/docs/getting-started)

## Next Steps

For SDK patterns and best practices, see `maintainx-sdk-patterns`.
