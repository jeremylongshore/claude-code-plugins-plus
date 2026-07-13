# Customer.io Webhooks & Events - Implementation Guide

## Webhook Event Types

```typescript
// types/customerio-webhooks.ts
export type WebhookEventType =
  | 'email_sent'
  | 'email_delivered'
  | 'email_opened'
  | 'email_clicked'
  | 'email_bounced'
  | 'email_complained'
  | 'email_unsubscribed'
  | 'email_converted'
  | 'push_sent'
  | 'push_delivered'
  | 'push_opened'
  | 'push_bounced'
  | 'sms_sent'
  | 'sms_delivered'
  | 'sms_failed'
  | 'in_app_opened'
  | 'in_app_clicked';

export interface WebhookEvent {
  event_id: string;
  object_type: 'email' | 'push' | 'sms' | 'in_app';
  metric: string;
  timestamp: number;
  data: {
    customer_id: string;
    email_address?: string;
    campaign_id?: number;
    action_id?: number;
    broadcast_id?: number;
    newsletter_id?: number;
    transactional_message_id?: number;
    delivery_id: string;
    subject?: string;
    link?: string;
    recipient?: string;
    identifiers?: {
      id?: string;
      email?: string;
    };
  };
}

export interface WebhookPayload {
  events: WebhookEvent[];
}
```

## Webhook Handler with Signature Verification

```typescript
// lib/webhook-handler.ts
import crypto from 'crypto';
import { Request, Response } from 'express';
import type { WebhookPayload, WebhookEvent } from '../types/customerio-webhooks';

export class CustomerIOWebhookHandler {
  private signingSecret: string;

  constructor(signingSecret: string) {
    this.signingSecret = signingSecret;
  }

  verifySignature(payload: string, signature: string): boolean {
    const expectedSignature = crypto
      .createHmac('sha256', this.signingSecret)
      .update(payload)
      .digest('hex');

    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(expectedSignature)
    );
  }

  async handleRequest(req: Request, res: Response): Promise<void> {
    const signature = req.headers['x-cio-signature'] as string;
    const payload = JSON.stringify(req.body);

    if (!signature || !this.verifySignature(payload, signature)) {
      res.status(401).json({ error: 'Invalid signature' });
      return;
    }

    const webhookPayload: WebhookPayload = req.body;

    try {
      await this.processEvents(webhookPayload.events);
      res.status(200).json({ processed: webhookPayload.events.length });
    } catch (error: any) {
      console.error('Webhook processing error:', error);
      res.status(500).json({ error: error.message });
    }
  }

  async processEvents(events: WebhookEvent[]): Promise<void> {
    for (const event of events) {
      await this.processEvent(event);
    }
  }

  async processEvent(event: WebhookEvent): Promise<void> {
    console.log(`Processing event: ${event.metric}`, event.event_id);

    switch (event.metric) {
      case 'email_delivered':
        await this.onEmailDelivered(event);
        break;
      case 'email_opened':
        await this.onEmailOpened(event);
        break;
      case 'email_clicked':
        await this.onEmailClicked(event);
        break;
      case 'email_bounced':
        await this.onEmailBounced(event);
        break;
      case 'email_complained':
        await this.onEmailComplained(event);
        break;
      case 'email_unsubscribed':
        await this.onEmailUnsubscribed(event);
        break;
      default:
        console.log(`Unhandled event type: ${event.metric}`);
    }
  }

  async onEmailDelivered(event: WebhookEvent): Promise<void> {
    console.log(`Email delivered to ${event.data.email_address}`);
  }

  async onEmailOpened(event: WebhookEvent): Promise<void> {
    console.log(`Email opened by ${event.data.customer_id}`);
  }

  async onEmailClicked(event: WebhookEvent): Promise<void> {
    console.log(`Link clicked: ${event.data.link}`);
  }

  async onEmailBounced(event: WebhookEvent): Promise<void> {
    console.log(`Email bounced for ${event.data.email_address}`);
  }

  async onEmailComplained(event: WebhookEvent): Promise<void> {
    console.log(`Spam complaint from ${event.data.email_address}`);
  }

  async onEmailUnsubscribed(event: WebhookEvent): Promise<void> {
    console.log(`User unsubscribed: ${event.data.customer_id}`);
  }
}
```

## Express Router Setup

```typescript
// routes/webhooks.ts
import { Router } from 'express';
import { CustomerIOWebhookHandler } from '../lib/webhook-handler';

const router = Router();
const webhookHandler = new CustomerIOWebhookHandler(
  process.env.CUSTOMERIO_WEBHOOK_SECRET!
);

router.use('/customerio', express.raw({ type: 'application/json' }));

router.post('/customerio', async (req, res) => {
  req.body = JSON.parse(req.body.toString());
  await webhookHandler.handleRequest(req, res);
});

export default router;
```

## Event Queue for Reliability

```typescript
// lib/webhook-queue.ts
import { Queue, Worker } from 'bullmq';
import Redis from 'ioredis';
import type { WebhookEvent } from '../types/customerio-webhooks';

const connection = new Redis(process.env.REDIS_URL!);

const webhookQueue = new Queue('customerio-webhooks', { connection });

export async function queueWebhookEvent(event: WebhookEvent): Promise<void> {
  await webhookQueue.add(event.metric, event, {
    removeOnComplete: 1000,
    removeOnFail: 5000,
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000
    }
  });
}

const worker = new Worker(
  'customerio-webhooks',
  async (job) => {
    const event: WebhookEvent = job.data;
    console.log(`Processing ${event.metric} event:`, event.event_id);

    switch (event.metric) {
      case 'email_bounced':
        await handleBounce(event);
        break;
      case 'email_complained':
        await handleComplaint(event);
        break;
    }
  },
  { connection }
);

worker.on('completed', (job) => {
  console.log(`Job ${job.id} completed`);
});

worker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed:`, err);
});
```

## Reporting API Integration

```typescript
// lib/customerio-reporting.ts
import { APIClient, RegionUS } from '@customerio/track';

const apiClient = new APIClient(process.env.CUSTOMERIO_APP_API_KEY!, {
  region: RegionUS
});

export async function getDeliveryMetrics(
  period: 'day' | 'week' | 'month' = 'day'
): Promise<DeliveryMetrics> {
  const response = await fetch(
    `https://api.customer.io/v1/metrics/email/${period}`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.CUSTOMERIO_APP_API_KEY}`
      }
    }
  );

  return response.json();
}

export async function getCampaignMetrics(campaignId: number): Promise<CampaignMetrics> {
  const response = await fetch(
    `https://api.customer.io/v1/campaigns/${campaignId}/metrics`,
    {
      headers: {
        'Authorization': `Bearer ${process.env.CUSTOMERIO_APP_API_KEY}`
      }
    }
  );

  return response.json();
}
```

## Data Warehouse Streaming

```typescript
// lib/event-streaming.ts
import { BigQuery } from '@google-cloud/bigquery';
import type { WebhookEvent } from '../types/customerio-webhooks';

const bigquery = new BigQuery();
const dataset = bigquery.dataset('customerio_events');
const table = dataset.table('delivery_events');

export async function streamToBigQuery(events: WebhookEvent[]): Promise<void> {
  const rows = events.map(event => ({
    event_id: event.event_id,
    event_type: event.metric,
    customer_id: event.data.customer_id,
    email_address: event.data.email_address,
    campaign_id: event.data.campaign_id,
    delivery_id: event.data.delivery_id,
    timestamp: new Date(event.timestamp * 1000).toISOString(),
    inserted_at: new Date().toISOString()
  }));

  await table.insert(rows);
}
```
