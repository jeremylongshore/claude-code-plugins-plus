# Guidewire Webhooks & Events - Implementation Guide

## App Events Architecture

```
+------------------+      +------------------+      +------------------+
|                  |      |                  |      |                  |
|  InsuranceSuite  |----->|   App Events     |----->|  Your System     |
|  (PC/CC/BC)      |      |   Service        |      |  (Webhook/Queue) |
|                  |      |                  |      |                  |
+------------------+      +------------------+      +------------------+
        |                         |                         |
        v                         v                         v
  Business Event             Kafka Topic              Event Handler
  (Policy Issued)            (Buffered)              (Process Event)
```

## Instructions

### Step 1: Configure App Events in Cloud Console

```yaml
# App Events Configuration
# Navigate to: Integration Gateway > App Events

events:
  - name: policy.issued
    description: Triggered when a policy is issued
    application: PolicyCenter
    entity: Policy
    payload:
      include:
        - policyNumber
        - effectiveDate
        - expirationDate
        - totalPremium
        - accountNumber
        - insuredName
    delivery:
      type: webhook
      endpoint: https://your-api.com/webhooks/guidewire
      retryPolicy:
        maxAttempts: 5
        backoffMultiplier: 2
        initialDelaySeconds: 10

  - name: claim.created
    description: Triggered when a new claim is filed
    application: ClaimCenter
    entity: Claim
    payload:
      include:
        - claimNumber
        - lossDate
        - lossType
        - policyNumber
        - status
    delivery:
      type: integration_gateway
      route: claim-processor
```

### Step 2: Webhook Receiver Implementation

```typescript
// Express.js webhook receiver
import express from 'express';
import crypto from 'crypto';
import { Redis } from 'ioredis';

const app = express();
const redis = new Redis(process.env.REDIS_URL);

// IMPORTANT: Raw body needed for signature verification
app.post('/webhooks/guidewire',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    const signature = req.headers['x-gw-signature'] as string;
    const timestamp = req.headers['x-gw-timestamp'] as string;
    const eventId = req.headers['x-gw-event-id'] as string;

    // Verify signature
    if (!verifySignature(req.body, signature, timestamp)) {
      console.error('Invalid signature');
      return res.status(401).json({ error: 'Invalid signature' });
    }

    // Check for replay attacks
    if (!await isTimestampValid(timestamp)) {
      return res.status(401).json({ error: 'Timestamp too old' });
    }

    // Ensure idempotency
    if (await isEventProcessed(eventId)) {
      console.log(`Event ${eventId} already processed`);
      return res.status(200).json({ status: 'already_processed' });
    }

    try {
      const event = JSON.parse(req.body.toString());
      await handleGuidewireEvent(event);
      await markEventProcessed(eventId);

      res.status(200).json({ status: 'processed' });
    } catch (error) {
      console.error('Event processing failed:', error);
      // Return 500 to trigger retry
      res.status(500).json({ error: 'Processing failed' });
    }
  }
);

function verifySignature(
  payload: Buffer,
  signature: string,
  timestamp: string
): boolean {
  const secret = process.env.GW_WEBHOOK_SECRET!;

  // Validate timestamp age (max 5 minutes)
  const timestampAge = Date.now() - parseInt(timestamp) * 1000;
  if (timestampAge > 300000) {
    return false;
  }

  // Compute expected signature
  const signedPayload = `${timestamp}.${payload.toString()}`;
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(signedPayload)
    .digest('hex');

  // Timing-safe comparison
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(`v1=${expectedSignature}`)
  );
}

async function isEventProcessed(eventId: string): Promise<boolean> {
  const key = `gw:event:${eventId}`;
  return (await redis.exists(key)) === 1;
}

async function markEventProcessed(eventId: string): Promise<void> {
  const key = `gw:event:${eventId}`;
  await redis.set(key, '1', 'EX', 86400 * 7); // 7 days TTL
}
```

### Step 3: Event Handler Implementation

```typescript
// Event handler with type safety
interface GuidewireEvent {
  id: string;
  type: string;
  timestamp: string;
  application: 'PolicyCenter' | 'ClaimCenter' | 'BillingCenter';
  data: Record<string, any>;
}

interface PolicyIssuedEvent extends GuidewireEvent {
  type: 'policy.issued';
  data: {
    policyNumber: string;
    effectiveDate: string;
    expirationDate: string;
    totalPremium: { amount: number; currency: string };
    accountNumber: string;
    insuredName: string;
  };
}

interface ClaimCreatedEvent extends GuidewireEvent {
  type: 'claim.created';
  data: {
    claimNumber: string;
    lossDate: string;
    lossType: string;
    policyNumber: string;
    status: string;
  };
}

type EventHandler<T extends GuidewireEvent> = (event: T) => Promise<void>;

const eventHandlers: Record<string, EventHandler<any>> = {
  'policy.issued': async (event: PolicyIssuedEvent) => {
    console.log(`Processing policy issued: ${event.data.policyNumber}`);

    // Update CRM
    await crmClient.updatePolicy({
      policyNumber: event.data.policyNumber,
      effectiveDate: event.data.effectiveDate,
      premium: event.data.totalPremium.amount
    });

    // Send welcome email
    await emailService.sendWelcomeEmail({
      to: event.data.insuredName,
      policyNumber: event.data.policyNumber,
      effectiveDate: event.data.effectiveDate
    });

    // Update analytics
    await analyticsService.trackPolicyIssued(event.data);
  },

  'claim.created': async (event: ClaimCreatedEvent) => {
    console.log(`Processing claim created: ${event.data.claimNumber}`);

    // Notify claims team
    await notificationService.notifyClaimsTeam({
      claimNumber: event.data.claimNumber,
      policyNumber: event.data.policyNumber,
      lossDate: event.data.lossDate
    });

    // Create task in task management system
    await taskService.createTask({
      type: 'REVIEW_CLAIM',
      reference: event.data.claimNumber,
      priority: determineClaimPriority(event.data)
    });
  }
};

async function handleGuidewireEvent(event: GuidewireEvent): Promise<void> {
  const handler = eventHandlers[event.type];

  if (!handler) {
    console.log(`No handler for event type: ${event.type}`);
    return;
  }

  await handler(event);
  console.log(`Processed event: ${event.type} (${event.id})`);
}
```

### Step 4: Gosu Event Publisher

```gosu
// Publishing custom events from Gosu
package gw.events

uses gw.api.messaging.MessageTransport
uses gw.api.util.Logger
uses gw.pl.persistence.core.Bundle

class CustomEventPublisher {
  private static final var LOG = Logger.forCategory("CustomEventPublisher")

  // Publish event when policy state changes
  static function publishPolicyEvent(policy : Policy, eventType : String) {
    var event = buildPolicyEvent(policy, eventType)
    publishEvent(event)
  }

  // Publish event when claim status changes
  static function publishClaimEvent(claim : Claim, eventType : String) {
    var event = buildClaimEvent(claim, eventType)
    publishEvent(event)
  }

  private static function buildPolicyEvent(policy : Policy, eventType : String) : Map<String, Object> {
    return {
      "eventType" -> eventType,
      "timestamp" -> Date.Now.toString(),
      "application" -> "PolicyCenter",
      "data" -> {
        "policyNumber" -> policy.PolicyNumber,
        "accountNumber" -> policy.Account.AccountNumber,
        "effectiveDate" -> policy.EffectiveDate.toString(),
        "expirationDate" -> policy.ExpirationDate.toString(),
        "status" -> policy.Status.Code,
        "totalPremium" -> {
          "amount" -> policy.TotalPremiumRPT.Amount,
          "currency" -> policy.TotalPremiumRPT.Currency.Code
        }
      }
    }
  }

  private static function buildClaimEvent(claim : Claim, eventType : String) : Map<String, Object> {
    return {
      "eventType" -> eventType,
      "timestamp" -> Date.Now.toString(),
      "application" -> "ClaimCenter",
      "data" -> {
        "claimNumber" -> claim.ClaimNumber,
        "policyNumber" -> claim.Policy.PolicyNumber,
        "lossDate" -> claim.LossDate.toString(),
        "lossType" -> claim.LossType.Code,
        "status" -> claim.State.Code
      }
    }
  }

  private static function publishEvent(event : Map<String, Object>) {
    try {
      // Publish to message destination
      var transport = MessageTransport.getInstance()
      var message = new gw.api.messaging.Message()
      message.Destination = "ExternalEventDestination"
      message.Body = gw.api.json.JsonObject.toJson(event)

      transport.send(message)
      LOG.info("Published event: ${event.get('eventType')}")
    } catch (e : Exception) {
      LOG.error("Failed to publish event", e)
      throw e
    }
  }
}
```

### Step 5: Integration Gateway Route

```yaml
# Integration Gateway route configuration
# config/integration/routes/claim-processor.yaml

route:
  name: claim-processor
  description: Process incoming claim events

  from:
    type: app-events
    event: claim.created

  steps:
    - transform:
        type: gosu
        class: gw.integration.transform.ClaimEventTransformer

    - filter:
        condition: ${body.data.lossType != 'test'}

    - choice:
        when:
          - condition: ${body.data.totalLoss == true}
            to:
              type: http
              url: https://external-system.com/total-loss
              method: POST
          - condition: ${body.data.subrogation == true}
            to:
              type: http
              url: https://external-system.com/subrogation
              method: POST
        otherwise:
          to:
            type: http
            url: https://external-system.com/standard-claim
            method: POST

  errorHandler:
    type: retry
    maxAttempts: 3
    delay: 5000
    onExhausted:
      type: dead-letter
      destination: claim-processing-dlq
```

### Step 6: Event Monitoring

```typescript
// Monitor event processing
interface EventMetrics {
  totalReceived: number;
  totalProcessed: number;
  totalFailed: number;
  processingTimeMs: number[];
  eventsByType: Record<string, number>;
  failuresByType: Record<string, number>;
}

class EventMonitor {
  private metrics: EventMetrics = {
    totalReceived: 0,
    totalProcessed: 0,
    totalFailed: 0,
    processingTimeMs: [],
    eventsByType: {},
    failuresByType: {}
  };

  recordEvent(eventType: string, success: boolean, durationMs: number): void {
    this.metrics.totalReceived++;
    this.metrics.eventsByType[eventType] = (this.metrics.eventsByType[eventType] || 0) + 1;

    if (success) {
      this.metrics.totalProcessed++;
      this.metrics.processingTimeMs.push(durationMs);
    } else {
      this.metrics.totalFailed++;
      this.metrics.failuresByType[eventType] = (this.metrics.failuresByType[eventType] || 0) + 1;
    }
  }

  getMetrics(): EventMetrics & { avgProcessingTimeMs: number; successRate: number } {
    const avgProcessingTimeMs = this.metrics.processingTimeMs.length > 0
      ? this.metrics.processingTimeMs.reduce((a, b) => a + b, 0) / this.metrics.processingTimeMs.length
      : 0;

    const successRate = this.metrics.totalReceived > 0
      ? this.metrics.totalProcessed / this.metrics.totalReceived
      : 0;

    return {
      ...this.metrics,
      avgProcessingTimeMs,
      successRate
    };
  }

  toPrometheus(): string {
    return `
# HELP gw_events_received_total Total events received
# TYPE gw_events_received_total counter
gw_events_received_total ${this.metrics.totalReceived}

# HELP gw_events_processed_total Successfully processed events
# TYPE gw_events_processed_total counter
gw_events_processed_total ${this.metrics.totalProcessed}

# HELP gw_events_failed_total Failed events
# TYPE gw_events_failed_total counter
gw_events_failed_total ${this.metrics.totalFailed}
`.trim();
  }
}
```

## Event Types Reference

| Application | Event Type | Trigger |
|-------------|------------|---------|
| PolicyCenter | policy.created | New policy bound |
| PolicyCenter | policy.issued | Policy issued |
| PolicyCenter | policy.cancelled | Policy cancelled |
| PolicyCenter | policy.renewed | Policy renewed |
| PolicyCenter | submission.quoted | Quote generated |
| ClaimCenter | claim.created | FNOL submitted |
| ClaimCenter | claim.closed | Claim closed |
| ClaimCenter | payment.issued | Payment created |
| BillingCenter | invoice.created | Invoice generated |
| BillingCenter | payment.received | Payment received |
