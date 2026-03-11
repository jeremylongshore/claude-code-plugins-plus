# Customerio Hello World - Implementation Guide

# Customer.io Hello World

## Overview
Create a minimal working Customer.io example that identifies a user and triggers an event.

## Prerequisites
- Completed `customerio-install-auth` skill
- Customer.io SDK installed
- Valid Site ID and API Key configured

## Instructions

### Step 1: Create Basic Integration
```typescript
// hello-customerio.ts
import { TrackClient, RegionUS } from '@customerio/track';

const client = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_API_KEY!,
  { region: RegionUS }
);

async function main() {
  // Step 1: Identify a user
  await client.identify('user-123', {
    email: 'hello@example.com',
    first_name: 'Hello',
    created_at: Math.floor(Date.now() / 1000)
  });
  console.log('User identified');

  // Step 2: Track an event
  await client.track('user-123', {
    name: 'hello_world',
    data: {
      source: 'sdk-test',
      timestamp: new Date().toISOString()
    }
  });
  console.log('Event tracked');
}

main().catch(console.error);
```

### Step 2: Run the Example
```bash
npx ts-node hello-customerio.ts
```

### Step 3: Verify in Dashboard
1. Go to Customer.io dashboard
2. Navigate to People section
3. Search for "user-123" or "hello@example.com"
4. Verify user profile shows attributes
5. Check Activity tab for "hello_world" event

## Output
- User created/updated in Customer.io
- Event recorded in user's activity log
- Console output confirming success

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid credentials | Verify Site ID and API Key |
| 400 Bad Request | Invalid data format | Check attribute names and types |
| User not found | Identify not called | Always identify before tracking events |
| Event not showing | Dashboard delay | Wait 1-2 minutes and refresh |

## Examples

### Python Hello World
```python
import os
from customerio import CustomerIO

cio = CustomerIO(
    site_id=os.environ.get('CUSTOMERIO_SITE_ID'),
    api_key=os.environ.get('CUSTOMERIO_API_KEY')
)

# Identify user
cio.identify(id='user-123', email='hello@example.com', first_name='Hello')
print('User identified')

# Track event
cio.track(customer_id='user-123', name='hello_world', source='sdk-test')
print('Event tracked')
```

### With Anonymous User
```typescript
// Track anonymous user with device ID
await client.identify('device-abc123', {
  anonymous_id: 'device-abc123',
  platform: 'web'
});
```

## Resources
- [Identify API](https://customer.io/docs/api/track/#operation/identify)
- [Track API](https://customer.io/docs/api/track/#operation/track)

## Next Steps
After verifying hello world works, proceed to `customerio-local-dev-loop` to set up your development workflow.
