# Customerio Install Auth - Implementation Guide

# Customer.io Install & Auth

## Overview
Set up Customer.io SDK and configure authentication credentials for email, push, SMS, and in-app messaging automation.

## Prerequisites
- Node.js 18+ or Python 3.10+
- Package manager (npm, pnpm, or pip)
- Customer.io account with API access
- Site ID and API Key from Customer.io dashboard

## Instructions

### Step 1: Install SDK
```bash
# Node.js (Track API)
npm install customerio-node

# Node.js (Journeys Track API - recommended)
npm install @customerio/track

# Python
pip install customerio
```

### Step 2: Configure Authentication
```bash
# Set environment variables
export CUSTOMERIO_SITE_ID="your-site-id"
export CUSTOMERIO_API_KEY="your-api-key"

# Or create .env file
cat >> .env << 'EOF'
CUSTOMERIO_SITE_ID=your-site-id
CUSTOMERIO_API_KEY=your-api-key
EOF
```

### Step 3: Verify Connection
```typescript
import { TrackClient, RegionUS } from '@customerio/track';

const client = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID,
  process.env.CUSTOMERIO_API_KEY,
  { region: RegionUS }
);

// Test by identifying a user
await client.identify('test-user', { email: 'test@example.com' });
console.log('Customer.io connection successful');
```

## Output
- Installed SDK package in node_modules or site-packages
- Environment variables or .env file with Site ID and API Key
- Successful connection verification output

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Invalid API Key | Incorrect or expired key | Verify key in Customer.io Settings > API Credentials |
| Invalid Site ID | Wrong site identifier | Check Site ID in Customer.io Settings |
| 401 Unauthorized | Authentication failed | Ensure both Site ID and API Key are correct |
| Network Error | Firewall blocking | Ensure outbound HTTPS to track.customer.io allowed |
| Module Not Found | Installation failed | Run `npm install` or `pip install` again |

## Examples

### TypeScript Setup
```typescript
import { TrackClient, RegionUS, RegionEU } from '@customerio/track';

// US region (default)
const client = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_API_KEY!,
  { region: RegionUS }
);

// EU region
const euClient = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_API_KEY!,
  { region: RegionEU }
);
```

### Python Setup
```python
import os
from customerio import CustomerIO

cio = CustomerIO(
    site_id=os.environ.get('CUSTOMERIO_SITE_ID'),
    api_key=os.environ.get('CUSTOMERIO_API_KEY')
)
```

## Resources
- [Customer.io Documentation](https://customer.io/docs/)
- [Track API Reference](https://customer.io/docs/api/track/)
- [Customer.io Status](https://status.customer.io/)

## Next Steps
After successful auth, proceed to `customerio-hello-world` for your first API call.
