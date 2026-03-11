# Apollo Webhooks Events - Implementation Guide

> Full implementation details and code examples for the `apollo-webhooks-events` skill.

# Apollo Webhooks Events

## Overview
Implement webhook handlers for Apollo.io to receive real-time notifications about contact updates, sequence events, and engagement activities.

## Apollo Webhook Events

| Event Type | Description | Payload Contains |
|------------|-------------|------------------|
| `contact.created` | New contact added | Contact data |
| `contact.updated` | Contact info changed | Updated fields |
| `sequence.started` | Contact added to sequence | Sequence & contact IDs |
| `sequence.completed` | Sequence finished | Completion status |
| `email.sent` | Email delivered | Email & contact info |
| `email.opened` | Email was opened | Open timestamp |
| `email.clicked` | Link clicked | Click details |
| `email.replied` | Reply received | Reply content |
| `email.bounced` | Email bounced | Bounce reason |

## Webhook Handler Implementation

### Express Handler
```typescript
// src/routes/webhooks/apollo.ts
import { Router } from 'express';
import crypto from 'crypto';
import { z } from 'zod';

const router = Router();

// Webhook payload schemas
const ContactEventSchema = z.object({
  event: z.enum(['contact.created', 'contact.updated']),
  timestamp: z.string(),
  data: z.object({
    contact: z.object({
      id: z.string(),
      email: z.string().optional(),
      name: z.string().optional(),
      title: z.string().optional(),
      organization: z.object({
        name: z.string(),
      }).optional(),
    }),
    changes: z.record(z.any()).optional(),
  }),
});

const SequenceEventSchema = z.object({
  event: z.enum(['sequence.started', 'sequence.completed', 'sequence.paused']),
  timestamp: z.string(),
  data: z.object({
    sequence_id: z.string(),
    contact_id: z.string(),
    status: z.string().optional(),
  }),
});

const EmailEventSchema = z.object({
  event: z.enum(['email.sent', 'email.opened', 'email.clicked', 'email.replied', 'email.bounced']),
  timestamp: z.string(),
  data: z.object({
    email_id: z.string(),
    contact_id: z.string(),
    sequence_id: z.string().optional(),
    subject: z.string().optional(),
    link_url: z.string().optional(), // For click events
    bounce_reason: z.string().optional(), // For bounce events
  }),
});

// Verify webhook signature
function verifySignature(payload: string, signature: string, secret: string): boolean {
  const expectedSignature = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expectedSignature)
  );
}

// Middleware for signature verification
function verifyApolloWebhook(req: any, res: any, next: any) {
  const signature = req.headers['x-apollo-signature'];
  const webhookSecret = process.env.APOLLO_WEBHOOK_SECRET;

  if (!webhookSecret) {
    console.error('APOLLO_WEBHOOK_SECRET not configured');
    return res.status(500).json({ error: 'Webhook secret not configured' });
  }

  if (!signature) {
    return res.status(401).json({ error: 'Missing signature' });
  }

  const rawBody = JSON.stringify(req.body);
  if (!verifySignature(rawBody, signature, webhookSecret)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  next();
}

// Main webhook endpoint
router.post('/apollo', verifyApolloWebhook, async (req, res) => {
  const { event } = req.body;

  try {
    // Route to appropriate handler
    if (event.startsWith('contact.')) {
      await handleContactEvent(ContactEventSchema.parse(req.body));
    } else if (event.startsWith('sequence.')) {
      await handleSequenceEvent(SequenceEventSchema.parse(req.body));
    } else if (event.startsWith('email.')) {
      await handleEmailEvent(EmailEventSchema.parse(req.body));
    } else {
      console.warn('Unknown event type:', event);
    }

    res.status(200).json({ received: true });
  } catch (error: any) {
    console.error('Webhook processing error:', error);
    res.status(400).json({ error: error.message });
  }
});

export default router;
```

### Event Handlers
```typescript
// src/services/webhooks/handlers.ts
import { prisma } from '../db';
import { publishEvent } from '../events';

export async function handleContactEvent(payload: any) {
  const { event, data } = payload;

  switch (event) {
    case 'contact.created':
      // Sync new contact to local database
      await prisma.contact.upsert({
        where: { apolloId: data.contact.id },
        create: {
          apolloId: data.contact.id,
          email: data.contact.email,
          name: data.contact.name,
          title: data.contact.title,
          company: data.contact.organization?.name,
          syncedAt: new Date(),
        },
        update: {
          email: data.contact.email,
          name: data.contact.name,
          title: data.contact.title,
          company: data.contact.organization?.name,
          syncedAt: new Date(),
        },
      });

      await publishEvent('apollo.contact.synced', {
        contactId: data.contact.id,
        action: 'created',
      });
      break;

    case 'contact.updated':
      await prisma.contact.update({
        where: { apolloId: data.contact.id },
        data: {
          ...data.changes,
          syncedAt: new Date(),
        },
      });

      await publishEvent('apollo.contact.synced', {
        contactId: data.contact.id,
        action: 'updated',
        changes: data.changes,
      });
      break;
  }
}

export async function handleSequenceEvent(payload: any) {
  const { event, data } = payload;

  switch (event) {
    case 'sequence.started':
      await prisma.sequenceEnrollment.create({
        data: {
          apolloContactId: data.contact_id,
          apolloSequenceId: data.sequence_id,
          status: 'active',
          startedAt: new Date(),
        },
      });
      break;

    case 'sequence.completed':
      await prisma.sequenceEnrollment.update({
        where: {
          apolloContactId_apolloSequenceId: {
            apolloContactId: data.contact_id,
            apolloSequenceId: data.sequence_id,
          },
        },
        data: {
          status: data.status || 'completed',
          completedAt: new Date(),
        },
      });
      break;
  }
}

export async function handleEmailEvent(payload: any) {
  const { event, data, timestamp } = payload;

  // Record email engagement
  await prisma.emailEngagement.create({
    data: {
      apolloEmailId: data.email_id,
      apolloContactId: data.contact_id,
      apolloSequenceId: data.sequence_id,
      eventType: event.replace('email.', ''),
      eventData: {
        subject: data.subject,
        linkUrl: data.link_url,
        bounceReason: data.bounce_reason,
      },
      occurredAt: new Date(timestamp),
    },
  });

  // Handle specific events
  if (event === 'email.replied') {
    // Notify sales team
    await publishEvent('apollo.lead.engaged', {
      contactId: data.contact_id,
      type: 'reply',
    });
  } else if (event === 'email.bounced') {
    // Mark contact as bounced
    await prisma.contact.update({
      where: { apolloId: data.contact_id },
      data: { emailStatus: 'bounced' },
    });
  }
}
```

## Webhook Registration

```typescript
// scripts/register-webhooks.ts
import { apollo } from '../src/lib/apollo/client';

interface WebhookConfig {
  url: string;
  events: string[];
  secret: string;
}

async function registerWebhook(config: WebhookConfig) {
  // Note: Apollo webhook registration is typically done through the UI
  // This is a placeholder for future API support
  console.log('Webhook registration:', config);

  // For now, provide instructions
  console.log(`
To register webhooks in Apollo:

1. Go to Apollo Settings > Integrations > Webhooks
2. Click "Add Webhook"
3. Enter URL: ${config.url}
4. Select events: ${config.events.join(', ')}
5. Copy the webhook secret and add to your environment:
   APOLLO_WEBHOOK_SECRET=<secret>
  `);
}

const webhookConfig: WebhookConfig = {
  url: `${process.env.APP_URL}/webhooks/apollo`,
  events: [
    'contact.created',
    'contact.updated',
    'sequence.started',
    'sequence.completed',
    'email.sent',
    'email.opened',
    'email.clicked',
    'email.replied',
    'email.bounced',
  ],
  secret: process.env.APOLLO_WEBHOOK_SECRET!,
};

registerWebhook(webhookConfig);
```

## Testing Webhooks

```typescript
// tests/webhooks/apollo.test.ts
import { describe, it, expect } from 'vitest';
import request from 'supertest';
import crypto from 'crypto';
import app from '../../src/app';

function signPayload(payload: any, secret: string): string {
  return crypto
    .createHmac('sha256', secret)
    .update(JSON.stringify(payload))
    .digest('hex');
}

describe('Apollo Webhooks', () => {
  const secret = 'test-webhook-secret';

  beforeAll(() => {
    process.env.APOLLO_WEBHOOK_SECRET = secret;
  });

  it('rejects requests without signature', async () => {
    const response = await request(app)
      .post('/webhooks/apollo')
      .send({ event: 'contact.created' });

    expect(response.status).toBe(401);
  });

  it('rejects requests with invalid signature', async () => {
    const response = await request(app)
      .post('/webhooks/apollo')
      .set('x-apollo-signature', 'invalid')
      .send({ event: 'contact.created' });

    expect(response.status).toBe(401);
  });

  it('processes contact.created event', async () => {
    const payload = {
      event: 'contact.created',
      timestamp: new Date().toISOString(),
      data: {
        contact: {
          id: 'test-123',
          email: 'test@example.com',
          name: 'Test User',
        },
      },
    };

    const signature = signPayload(payload, secret);

    const response = await request(app)
      .post('/webhooks/apollo')
      .set('x-apollo-signature', signature)
      .send(payload);

    expect(response.status).toBe(200);
    expect(response.body.received).toBe(true);
  });

  it('processes email.opened event', async () => {
    const payload = {
      event: 'email.opened',
      timestamp: new Date().toISOString(),
      data: {
        email_id: 'email-123',
        contact_id: 'contact-123',
        sequence_id: 'seq-123',
      },
    };

    const signature = signPayload(payload, secret);

    const response = await request(app)
      .post('/webhooks/apollo')
      .set('x-apollo-signature', signature)
      .send(payload);

    expect(response.status).toBe(200);
  });
});
```

## Local Testing with ngrok

```bash
# Start local server
npm run dev

# In another terminal, start ngrok
ngrok http 3000

# Use the ngrok URL for webhook registration
# Example: https://abc123.ngrok.io/webhooks/apollo
```

## Output
- Webhook endpoint with signature verification
- Event handlers for all Apollo event types
- Database sync for contact and engagement data
- Webhook registration instructions
- Test suite for webhook validation

## Error Handling
| Issue | Resolution |
|-------|------------|
| Invalid signature | Check webhook secret |
| Unknown event | Log and acknowledge (200) |
| Processing error | Log error, return 500 |
| Duplicate events | Implement idempotency |

## Resources
- [Apollo Webhooks Documentation](https://knowledge.apollo.io/hc/en-us/articles/4415154183053)
- [Webhook Security Best Practices](https://hookdeck.com/webhooks/guides/webhook-security-best-practices)
- [ngrok for Local Testing](https://ngrok.com/)

## Next Steps
Proceed to `apollo-performance-tuning` for optimization.
