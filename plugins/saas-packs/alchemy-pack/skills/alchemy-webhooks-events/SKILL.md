---
name: alchemy-webhooks-events
description: |
  Implement Alchemy Notify webhooks for real-time blockchain event notifications.
  Use when tracking wallet activity, monitoring mined transactions,
  watching smart contract events, or building real-time dApp features.
  Trigger: "alchemy webhook", "alchemy notify", "alchemy events",
  "alchemy address activity", "alchemy real-time notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, webhooks]
compatible-with: claude-code
---

# Alchemy Webhooks & Events (Notify API)

## Overview

Alchemy Notify provides real-time push notifications for on-chain events. Instead of polling, receive webhook callbacks for wallet activity, mined transactions, dropped transactions, and smart contract events.

## Webhook Types

| Type | Trigger | Use Case |
|------|---------|----------|
| Address Activity | ETH/token transfer to/from address | Wallet notifications |
| Mined Transaction | Transaction confirmed on-chain | Payment confirmation |
| Dropped Transaction | Transaction removed from mempool | Failed tx alerting |
| NFT Activity | NFT transfer events | Marketplace notifications |
| Custom Webhook | GraphQL-defined filter | Complex event tracking |

## Instructions

### Step 1: Create Webhook via Dashboard or API

```bash
# Create Address Activity webhook via Alchemy API
curl -X POST "https://dashboard.alchemy.com/api/create-webhook" \
  -H "X-Alchemy-Token: ${ALCHEMY_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "network": "ETH_MAINNET",
    "webhook_type": "ADDRESS_ACTIVITY",
    "webhook_url": "https://your-app.com/webhooks/alchemy",
    "addresses": [
      "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
    ]
  }'
```

### Step 2: Webhook Handler with Signature Verification

```typescript
// src/webhooks/alchemy-handler.ts
import express from 'express';
import crypto from 'crypto';

const router = express.Router();

router.post('/webhooks/alchemy',
  express.raw({ type: 'application/json' }),
  async (req, res) => {
    // Verify webhook signature
    const signature = req.headers['x-alchemy-signature'] as string;
    if (!verifySignature(req.body.toString(), signature)) {
      return res.status(401).json({ error: 'Invalid signature' });
    }

    const event = JSON.parse(req.body.toString());
    await processAlchemyEvent(event);
    res.status(200).json({ ok: true });
  }
);

function verifySignature(body: string, signature: string): boolean {
  const signingKey = process.env.ALCHEMY_WEBHOOK_SIGNING_KEY!;
  const hmac = crypto.createHmac('sha256', signingKey);
  hmac.update(body, 'utf8');
  const digest = hmac.digest('hex');
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(digest));
}
```

### Step 3: Event Router

```typescript
// src/webhooks/event-router.ts
interface AlchemyWebhookEvent {
  webhookId: string;
  id: string;
  createdAt: string;
  type: 'ADDRESS_ACTIVITY' | 'MINED_TRANSACTION' | 'DROPPED_TRANSACTION' | 'NFT_ACTIVITY';
  event: {
    network: string;
    activity: Array<{
      fromAddress: string;
      toAddress: string;
      value: number;
      asset: string;
      category: 'external' | 'internal' | 'erc20' | 'erc721' | 'erc1155';
      hash: string;
      blockNum: string;
    }>;
  };
}

async function processAlchemyEvent(event: AlchemyWebhookEvent): Promise<void> {
  switch (event.type) {
    case 'ADDRESS_ACTIVITY':
      for (const activity of event.event.activity) {
        console.log(`${activity.category} transfer: ${activity.value} ${activity.asset}`);
        console.log(`  From: ${activity.fromAddress}`);
        console.log(`  To: ${activity.toAddress}`);
        console.log(`  Tx: ${activity.hash}`);
        // Trigger application logic (e.g., update balance, send notification)
      }
      break;

    case 'MINED_TRANSACTION':
      console.log('Transaction mined:', event.event);
      break;

    case 'DROPPED_TRANSACTION':
      console.log('Transaction dropped:', event.event);
      // Alert user their transaction was dropped
      break;

    case 'NFT_ACTIVITY':
      for (const activity of event.event.activity) {
        console.log(`NFT transfer: ${activity.asset} #${activity.value}`);
      }
      break;
  }
}
```

### Step 4: Programmatic Webhook Management

```typescript
// src/webhooks/manage-webhooks.ts
import { Alchemy, Network, WebhookType } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
  authToken: process.env.ALCHEMY_AUTH_TOKEN, // Required for Notify API
});

async function setupAddressWebhook(addresses: string[], webhookUrl: string) {
  const webhook = await alchemy.notify.createWebhook(
    webhookUrl,
    WebhookType.ADDRESS_ACTIVITY,
    { addresses, network: Network.ETH_MAINNET }
  );
  console.log(`Webhook created: ${webhook.id}`);
  return webhook;
}

async function listWebhooks() {
  const webhooks = await alchemy.notify.getAllWebhooks();
  for (const wh of webhooks.webhooks) {
    console.log(`${wh.id}: ${wh.webhookType} → ${wh.webhookUrl} (${wh.isActive ? 'active' : 'inactive'})`);
  }
}

async function addAddressToWebhook(webhookId: string, newAddresses: string[]) {
  await alchemy.notify.updateWebhook(webhookId, {
    addAddresses: newAddresses,
  });
}
```

## Output

- Address Activity webhook for wallet monitoring
- HMAC signature verification for webhook security
- Event router handling all Alchemy webhook types
- Programmatic webhook management via Notify API

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong signing key | Copy from Alchemy webhook details page |
| Missing events | Webhook URL not reachable | Ensure HTTPS endpoint is publicly accessible |
| Duplicate events | No idempotency | Track webhook event IDs |

## Resources

- [Alchemy Webhooks Overview](https://www.alchemy.com/docs/reference/webhooks-overview)
- [Alchemy Webhook Types](https://www.alchemy.com/docs/reference/webhook-types)
- [Alchemy Notify Tutorial](https://github.com/alchemyplatform/Alchemy-Notify-Tutorial)

## Next Steps

For performance optimization, see `alchemy-performance-tuning`.
