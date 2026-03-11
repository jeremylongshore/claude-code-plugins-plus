# Customer.io Advanced Troubleshooting - Implementation Guide

### Step 1: API Debugging
```typescript
// lib/debug-client.ts
import { TrackClient, RegionUS } from '@customerio/track';

interface DebugResult {
  success: boolean;
  latency: number;
  requestId?: string;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}

export class DebugCustomerIO {
  private client: TrackClient;

  constructor() {
    this.client = new TrackClient(
      process.env.CUSTOMERIO_SITE_ID!,
      process.env.CUSTOMERIO_API_KEY!,
      { region: RegionUS }
    );
  }

  async debugIdentify(
    userId: string,
    attributes: Record<string, any>
  ): Promise<DebugResult> {
    const start = Date.now();

    console.log('=== Customer.io Debug: Identify ===');
    console.log('User ID:', userId);
    console.log('Attributes:', JSON.stringify(attributes, null, 2));

    try {
      await this.client.identify(userId, attributes);

      const result: DebugResult = {
        success: true,
        latency: Date.now() - start
      };

      console.log('Result: SUCCESS');
      console.log('Latency:', result.latency, 'ms');

      return result;
    } catch (error: any) {
      const result: DebugResult = {
        success: false,
        latency: Date.now() - start,
        error: {
          code: error.statusCode || 'UNKNOWN',
          message: error.message,
          details: error.response?.body
        }
      };

      console.log('Result: FAILED');
      console.log('Error:', JSON.stringify(result.error, null, 2));

      return result;
    }
  }

  async debugTrack(
    userId: string,
    event: string,
    data?: Record<string, any>
  ): Promise<DebugResult> {
    const start = Date.now();

    console.log('=== Customer.io Debug: Track ===');
    console.log('User ID:', userId);
    console.log('Event:', event);
    console.log('Data:', JSON.stringify(data, null, 2));

    try {
      await this.client.track(userId, { name: event, data });

      return {
        success: true,
        latency: Date.now() - start
      };
    } catch (error: any) {
      return {
        success: false,
        latency: Date.now() - start,
        error: {
          code: error.statusCode || 'UNKNOWN',
          message: error.message
        }
      };
    }
  }
}
```

### Step 2: User Profile Investigation
```typescript
// scripts/investigate-user.ts
interface UserInvestigation {
  userId: string;
  profile: {
    exists: boolean;
    attributes: Record<string, any>;
    segments: string[];
  };
  activity: {
    lastIdentify: Date;
    lastEvent: Date;
    eventCount24h: number;
    recentEvents: string[];
  };
  delivery: {
    emailsSent: number;
    emailsDelivered: number;
    emailsOpened: number;
    bounces: number;
    complaints: number;
    suppressed: boolean;
  };
  issues: string[];
}

async function investigateUser(userId: string): Promise<UserInvestigation> {
  const investigation: UserInvestigation = {
    userId,
    profile: { exists: false, attributes: {}, segments: [] },
    activity: {
      lastIdentify: new Date(0),
      lastEvent: new Date(0),
      eventCount24h: 0,
      recentEvents: []
    },
    delivery: {
      emailsSent: 0,
      emailsDelivered: 0,
      emailsOpened: 0,
      bounces: 0,
      complaints: 0,
      suppressed: false
    },
    issues: []
  };

  // 1. Check if user exists
  try {
    const profile = await fetchUserProfile(userId);
    investigation.profile = {
      exists: true,
      attributes: profile.attributes,
      segments: profile.segments
    };
  } catch (error) {
    investigation.issues.push('User profile not found in Customer.io');
    return investigation;
  }

  // 2. Check for missing required attributes
  if (!investigation.profile.attributes.email) {
    investigation.issues.push('User missing email attribute - cannot receive emails');
  }

  // 3. Check suppression status
  if (investigation.delivery.suppressed) {
    investigation.issues.push('User is suppressed - no messages will be sent');
  }

  // 4. Check bounce/complaint history
  if (investigation.delivery.bounces > 0) {
    investigation.issues.push(`User has ${investigation.delivery.bounces} bounces`);
  }

  if (investigation.delivery.complaints > 0) {
    investigation.issues.push(`User has ${investigation.delivery.complaints} spam complaints - HIGH PRIORITY`);
  }

  // 5. Check recent activity
  const oneDayAgo = new Date(Date.now() - 24 * 60 * 60 * 1000);
  if (investigation.activity.lastIdentify < oneDayAgo) {
    investigation.issues.push('User profile not updated in 24+ hours');
  }

  return investigation;
}
```

### Step 3: Campaign Debugging
```typescript
// scripts/debug-campaign.ts
interface CampaignDebug {
  campaignId: number;
  status: 'active' | 'paused' | 'draft';
  trigger: {
    type: string;
    conditions: any;
  };
  audience: {
    segmentId?: number;
    estimatedSize: number;
  };
  recentSends: Array<{
    userId: string;
    timestamp: Date;
    status: string;
  }>;
  issues: string[];
}

async function debugCampaign(campaignId: number): Promise<CampaignDebug> {
  const debug: CampaignDebug = {
    campaignId,
    status: 'draft',
    trigger: { type: '', conditions: {} },
    audience: { estimatedSize: 0 },
    recentSends: [],
    issues: []
  };

  // Fetch campaign details from API
  // Analyze trigger conditions
  // Check audience size
  // Review recent send activity

  // Common issues to check
  if (debug.status !== 'active') {
    debug.issues.push('Campaign is not active');
  }

  if (debug.audience.estimatedSize === 0) {
    debug.issues.push('No users match campaign audience');
  }

  return debug;
}
```

### Step 4: Webhook Debugging
```typescript
// lib/webhook-debugger.ts
import crypto from 'crypto';

interface WebhookDebugResult {
  signatureValid: boolean;
  payloadParsed: boolean;
  eventsProcessed: number;
  errors: Array<{
    event: string;
    error: string;
  }>;
  processingTime: number;
}

export function debugWebhook(
  rawBody: string,
  signature: string,
  secret: string
): WebhookDebugResult {
  const start = Date.now();
  const result: WebhookDebugResult = {
    signatureValid: false,
    payloadParsed: false,
    eventsProcessed: 0,
    errors: [],
    processingTime: 0
  };

  // 1. Verify signature
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(rawBody)
    .digest('hex');

  result.signatureValid = crypto.timingSafeEqual(
    Buffer.from(signature || ''),
    Buffer.from(expectedSignature)
  );

  if (!result.signatureValid) {
    console.log('Expected signature:', expectedSignature);
    console.log('Received signature:', signature);
    result.processingTime = Date.now() - start;
    return result;
  }

  // 2. Parse payload
  try {
    const payload = JSON.parse(rawBody);
    result.payloadParsed = true;

    // 3. Process events
    for (const event of payload.events || []) {
      try {
        console.log('Processing event:', event.metric, event.event_id);
        result.eventsProcessed++;
      } catch (error: any) {
        result.errors.push({
          event: event.event_id,
          error: error.message
        });
      }
    }
  } catch (error: any) {
    result.errors.push({
      event: 'parse',
      error: error.message
    });
  }

  result.processingTime = Date.now() - start;
  return result;
}
```

### Step 5: Network Debugging
```bash
#!/bin/bash
# scripts/debug-network.sh

echo "=== Customer.io Network Diagnostics ==="

# 1. DNS Resolution
echo -e "\n1. DNS Resolution:"
dig track.customer.io +short

# 2. TCP Connectivity
echo -e "\n2. TCP Connectivity:"
nc -zv track.customer.io 443 2>&1

# 3. TLS Handshake
echo -e "\n3. TLS Certificate:"
echo | openssl s_client -connect track.customer.io:443 2>/dev/null | openssl x509 -noout -dates

# 4. API Response Time
echo -e "\n4. API Latency:"
curl -o /dev/null -s -w "Connect: %{time_connect}s\nTTFB: %{time_starttransfer}s\nTotal: %{time_total}s\n" \
  -X POST "https://track.customer.io/api/v1/customers/test" \
  -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com"}'

# 5. Check for rate limiting
echo -e "\n5. Rate Limit Check:"
for i in {1..5}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST "https://track.customer.io/api/v1/customers/test-$i" \
    -u "$CUSTOMERIO_SITE_ID:$CUSTOMERIO_API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com"}'
done
```

### Step 6: Incident Response Runbook
```markdown
## Customer.io Incident Response Runbook

### P1: Complete API Outage
1. Check https://status.customer.io/
2. Verify credentials haven't expired
3. Test with curl directly
4. Enable circuit breaker if available
5. Queue events for retry
6. Notify stakeholders

### P2: High Error Rate (>5%)
1. Check error distribution by type
2. Identify affected operations
3. Review recent code deployments
4. Check for rate limiting
5. Scale down if self-inflicted

### P3: Delivery Issues
1. Check bounce/complaint rates
2. Review suppression list
3. Verify sender reputation
4. Check campaign configuration
5. Review segment conditions

### P4: Webhook Failures
1. Verify webhook secret
2. Check endpoint availability
3. Review payload format
4. Check for duplicate events
5. Verify idempotency handling
```

## Diagnostic Commands

```bash
# Check API health
curl -s "https://status.customer.io/api/v2/status.json" | jq '.status'

# Test authentication
curl -u "$CIO_SITE_ID:$CIO_API_KEY" "https://track.customer.io/api/v1/accounts"

# Check user exists
curl -u "$CIO_SITE_ID:$CIO_API_KEY" "https://track.customer.io/api/v1/customers/USER_ID"
```
