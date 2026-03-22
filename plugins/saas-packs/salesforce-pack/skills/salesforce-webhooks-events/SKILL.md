---
name: salesforce-webhooks-events
description: |
  Implement Salesforce Platform Events, Change Data Capture (CDC), and Outbound Messages.
  Use when building real-time integrations, listening for record changes,
  or implementing event-driven architecture with Salesforce.
  Trigger with phrases like "salesforce events", "salesforce CDC",
  "salesforce platform events", "salesforce streaming", "salesforce outbound message", "salesforce real-time".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(sf:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, salesforce]
compatible-with: claude-code
---

# Salesforce Webhooks & Events

## Overview
Salesforce doesn't use traditional webhooks. Instead, it offers Platform Events, Change Data Capture (CDC), and Outbound Messages for real-time data flow. All use the CometD (Bayeux) streaming protocol via jsforce.

## Prerequisites
- jsforce installed with connection configured
- Platform Events or CDC enabled in your org
- Understanding of publish/subscribe patterns
- Express.js for Outbound Message endpoints

## Event Mechanism Comparison

| Mechanism | Direction | Use Case | Retention |
|-----------|-----------|----------|-----------|
| Platform Events | Bi-directional | Custom event bus | 72 hours |
| Change Data Capture (CDC) | Salesforce → External | Record change notifications | 3 days |
| Outbound Messages | Salesforce → External | Workflow-triggered HTTP POST | Until confirmed |
| Streaming API (PushTopics) | Salesforce → External | SOQL-based subscriptions | No replay |

## Instructions

### Step 1: Subscribe to Change Data Capture (CDC)

```typescript
import jsforce from 'jsforce';

const conn = new jsforce.Connection({
  loginUrl: process.env.SF_LOGIN_URL,
});
await conn.login(process.env.SF_USERNAME!, process.env.SF_PASSWORD! + process.env.SF_SECURITY_TOKEN!);

// Subscribe to Account changes
// CDC channel format: /data/AccountChangeEvent
const subscription = conn.streaming.topic('/data/AccountChangeEvent').subscribe((message) => {
  const header = message.payload.ChangeEventHeader;
  console.log('Change Type:', header.changeType);       // CREATE, UPDATE, DELETE, UNDELETE
  console.log('Record IDs:', header.recordIds);
  console.log('Changed Fields:', header.changedFields);
  console.log('User ID:', header.commitUser);

  // Access changed field values
  if (header.changeType === 'UPDATE') {
    console.log('New values:', message.payload);
    // Only changed fields are populated in the payload
  }
});

// Enable CDC for objects in Setup:
// Setup > Integrations > Change Data Capture > Select Objects
```

### Step 2: Publish and Subscribe to Platform Events

```typescript
// Define a Platform Event in Salesforce:
// Setup > Platform Events > New Platform Event
// Example: Order_Status__e with fields:
//   - Order_Id__c (Text)
//   - Status__c (Text)
//   - Amount__c (Number)

// Publish a Platform Event via API
await conn.sobject('Order_Status__e').create({
  Order_Id__c: 'ORD-12345',
  Status__c: 'Shipped',
  Amount__c: 499.99,
});

// Subscribe to Platform Events
const eventSub = conn.streaming.topic('/event/Order_Status__e').subscribe((message) => {
  console.log('Event received:', {
    orderId: message.payload.Order_Id__c,
    status: message.payload.Status__c,
    amount: message.payload.Amount__c,
    replayId: message.event.replayId,
  });
});

// Use replayId to resume from a specific point (-1 = new only, -2 = all available)
conn.streaming.topic('/event/Order_Status__e', { replayId: -2 }).subscribe((message) => {
  // Receives all stored events (up to 72 hours)
});
```

### Step 3: Handle Outbound Messages (SOAP-based)

```typescript
// Outbound Messages are sent by Salesforce Workflow Rules or Flows
// They are SOAP XML posts to your endpoint

import express from 'express';
import { parseString } from 'xml2js';

const app = express();
app.use(express.text({ type: 'text/xml' }));

app.post('/salesforce/outbound-message', (req, res) => {
  parseString(req.body, (err, result) => {
    if (err) {
      console.error('XML parse error:', err);
      return res.status(400).send('Invalid XML');
    }

    // Extract notification data
    const notification = result['soapenv:Envelope']['soapenv:Body'][0]
      ['notifications'][0]['Notification'][0];

    const sobject = notification['sObject'][0];
    console.log('Record ID:', sobject['sf:Id'][0]);
    console.log('Object Type:', sobject.$['xsi:type']);

    // Respond with acknowledgment (required!)
    res.type('text/xml').send(`<?xml version="1.0" encoding="UTF-8"?>
      <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
        xmlns:out="http://soap.sforce.com/2005/09/outbound">
        <soapenv:Body>
          <out:notificationsResponse>
            <out:Ack>true</out:Ack>
          </out:notificationsResponse>
        </soapenv:Body>
      </soapenv:Envelope>`);
  });
});
```

### Step 4: Robust Event Processing

```typescript
// Idempotent event handler with replay ID tracking
import { Redis } from 'ioredis';
const redis = new Redis(process.env.REDIS_URL);

async function processEvent(message: any): Promise<void> {
  const replayId = message.event.replayId;
  const eventKey = `sf:event:${replayId}`;

  // Check if already processed (idempotency)
  if (await redis.exists(eventKey)) {
    console.log(`Event ${replayId} already processed, skipping`);
    return;
  }

  try {
    // Process the event
    const changeType = message.payload.ChangeEventHeader?.changeType;
    const recordIds = message.payload.ChangeEventHeader?.recordIds || [];

    switch (changeType) {
      case 'CREATE':
        await handleRecordCreated(recordIds, message.payload);
        break;
      case 'UPDATE':
        await handleRecordUpdated(recordIds, message.payload);
        break;
      case 'DELETE':
        await handleRecordDeleted(recordIds);
        break;
    }

    // Mark as processed with 7-day TTL
    await redis.set(eventKey, '1', 'EX', 86400 * 7);

    // Save replay ID for resume on restart
    await redis.set('sf:last-replay-id', replayId.toString());
  } catch (error) {
    console.error(`Failed to process event ${replayId}:`, error);
    throw error; // Let retry logic handle it
  }
}
```

## Output
- CDC subscription for real-time record change notifications
- Platform Event publishing and subscribing
- Outbound Message endpoint with SOAP acknowledgment
- Idempotent event processing with replay ID tracking

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| `403: CDC not enabled` | Object not selected for CDC | Setup > Change Data Capture > select objects |
| `EVENT_OR_PUSHTTOPIC_NOT_FOUND` | Platform Event doesn't exist | Create in Setup > Platform Events |
| Missed events | Client disconnected | Use `replayId` to resume from last position |
| Duplicate processing | No idempotency check | Track processed `replayId` values in Redis |
| Outbound Message retry | Ack not sent | Return `<Ack>true</Ack>` XML response |

## Resources
- [Change Data Capture Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.change_data_capture.meta/change_data_capture/)
- [Platform Events Developer Guide](https://developer.salesforce.com/docs/atlas.en-us.platform_events.meta/platform_events/)
- [Streaming API](https://developer.salesforce.com/docs/atlas.en-us.api_streaming.meta/api_streaming/)
- [Outbound Messaging](https://developer.salesforce.com/docs/atlas.en-us.api.meta/api/sforce_api_om_outboundmessaging.htm)

## Next Steps
For performance optimization, see `salesforce-performance-tuning`.
