# Local Development Setup

## Project Structure

```
my-retellai-project/
├── src/
│   ├── retellai/
│   │   ├── client.ts       # Retell AI client wrapper
│   │   ├── config.ts       # Configuration management
│   │   └── utils.ts        # Helper functions
│   └── index.ts
├── tests/
│   └── retellai.test.ts
├── .env.local              # Local secrets (git-ignored)
├── .env.example            # Template for team
└── package.json
```

## Environment Setup

```bash
set -euo pipefail
# Copy environment template
cp .env.example .env.local

# Install dependencies
npm install

# Start development server
npm run dev
```

## Hot Reload Configuration

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch"
  }
}
```

## Test Setup

```typescript
import { describe, it, expect, vi } from 'vitest';
import { RetellAIClient } from '../src/retellai/client';

describe('Retell AI Client', () => {
  it('should initialize with API key', () => {
    const client = new RetellAIClient({ apiKey: 'test-key' });
    expect(client).toBeDefined();
  });
});
```

## Mock Retell AI Responses

```typescript
vi.mock('@retellai/sdk', () => ({
  RetellAIClient: vi.fn().mockImplementation(() => ({
    // Mock methods here
  })),
}));
```

## Debug Mode

```bash
set -euo pipefail
# Enable verbose logging
DEBUG=RETELLAI=* npm run dev
```
