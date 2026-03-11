# Customerio Local Dev Loop - Implementation Guide

# Customer.io Local Dev Loop

## Overview
Set up an efficient local development workflow for Customer.io integrations with proper testing and isolation.

## Prerequisites
- Customer.io SDK installed
- Separate development workspace in Customer.io (recommended)
- Environment variable management tool (dotenv)

## Instructions

### Step 1: Create Environment Configuration
```bash
# .env.development
CUSTOMERIO_SITE_ID=dev-site-id
CUSTOMERIO_API_KEY=dev-api-key
CUSTOMERIO_REGION=us

# .env.production
CUSTOMERIO_SITE_ID=prod-site-id
CUSTOMERIO_API_KEY=prod-api-key
CUSTOMERIO_REGION=us
```

### Step 2: Create Dev Client Wrapper
```typescript
// lib/customerio.ts
import { TrackClient, RegionUS, RegionEU } from '@customerio/track';

const getRegion = () => {
  return process.env.CUSTOMERIO_REGION === 'eu' ? RegionEU : RegionUS;
};

const isDevelopment = process.env.NODE_ENV !== 'production';

class CustomerIOClient {
  private client: TrackClient;
  private dryRun: boolean;

  constructor() {
    this.client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_API_KEY!,
      { region: getRegion() }
    );
    this.dryRun = process.env.CUSTOMERIO_DRY_RUN === 'true';
  }

  async identify(userId: string, attributes: Record<string, any>) {
    if (this.dryRun) {
      console.log('[DRY RUN] Identify:', { userId, attributes });
      return;
    }
    if (isDevelopment) {
      attributes._dev = true;
      attributes._dev_timestamp = new Date().toISOString();
    }
    return this.client.identify(userId, attributes);
  }

  async track(userId: string, eventName: string, data?: Record<string, any>) {
    if (this.dryRun) {
      console.log('[DRY RUN] Track:', { userId, eventName, data });
      return;
    }
    const eventData = {
      name: isDevelopment ? `dev_${eventName}` : eventName,
      data: { ...data, _dev: isDevelopment }
    };
    return this.client.track(userId, eventData);
  }
}

export const cio = new CustomerIOClient();
```

### Step 3: Set Up Test Helpers
```typescript
// test/helpers/customerio-mock.ts
import { vi } from 'vitest';

export const mockCustomerIO = () => {
  const mocks = {
    identify: vi.fn().mockResolvedValue(undefined),
    track: vi.fn().mockResolvedValue(undefined),
    trackAnonymous: vi.fn().mockResolvedValue(undefined),
  };

  vi.mock('@customerio/track', () => ({
    TrackClient: vi.fn().mockImplementation(() => mocks),
    RegionUS: 'us',
    RegionEU: 'eu',
  }));

  return mocks;
};

// Usage in tests
import { mockCustomerIO } from './helpers/customerio-mock';

describe('User Registration', () => {
  const cioMocks = mockCustomerIO();

  it('identifies user on signup', async () => {
    await registerUser({ email: 'test@example.com' });
    expect(cioMocks.identify).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({ email: 'test@example.com' })
    );
  });
});
```

### Step 4: Create Dev Scripts
```json
{
  "scripts": {
    "dev:cio": "CUSTOMERIO_DRY_RUN=true ts-node scripts/test-customerio.ts",
    "dev:cio:live": "dotenv -e .env.development ts-node scripts/test-customerio.ts",
    "test:cio": "vitest run --reporter=verbose tests/customerio/"
  }
}
```

## Output
- Environment-aware Customer.io client
- Dry-run mode for safe testing
- Test mocks for unit testing
- Prefixed events for development isolation

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Wrong environment | Env vars not loaded | Use dotenv or env-specific files |
| Dev events in prod | Environment check failed | Verify NODE_ENV is set correctly |
| Mock not working | Import order issue | Mock before importing client |

## Resources
- [Customer.io Workspaces](https://customer.io/docs/workspaces/)
- [Test Mode Best Practices](https://customer.io/docs/test-mode/)

## Next Steps
After setting up local dev, proceed to `customerio-sdk-patterns` for production-ready patterns.
