---
name: quicknode-webhooks-events
description: |
  QuickNode webhooks events — blockchain RPC and Web3 infrastructure integration.
  Use when working with QuickNode for blockchain development.
  Trigger with phrases like "quicknode webhooks events", "quicknode-webhooks-events", "blockchain RPC".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, quicknode, blockchain, web3, rpc, ethereum]
compatible-with: claude-code, codex, openclaw
---

# QuickNode Webhooks Events

## Overview
Set up QuickNode Streams for real-time on-chain event processing with custom filters and webhook delivery.

## Prerequisites
- QuickNode account with Streams access
- HTTPS webhook endpoint

## Instructions

### Step 1: Create a Stream via Dashboard
```text
1. Dashboard > Streams > Create Stream
2. Select chain: Ethereum Mainnet
3. Filter: Contract events for specific address
4. Destination: Webhook URL
5. Set payload format: JSON
```

### Step 2: Handle Stream Events
```typescript
import express from 'express';

const app = express();
app.post('/webhooks/quicknode', express.json(), async (req, res) => {
  const events = req.body;
  for (const event of events) {
    console.log(`Block: ${event.blockNumber}`);
    console.log(`TX: ${event.transactionHash}`);
    console.log(`Topics: ${event.topics}`);
    // Process on-chain event
    await processBlockchainEvent(event);
  }
  res.status(200).json({ received: true });
});
```

### Step 3: Filter by Contract Events
```javascript
// Stream filter function (runs on QuickNode infrastructure)
function main(data) {
  const targetContract = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'; // USDC
  const transferTopic = '0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef';
  
  return data.streamData.filter(tx => {
    return tx.logs?.some(log =>
      log.address.toLowerCase() === targetContract.toLowerCase() &&
      log.topics[0] === transferTopic
    );
  });
}
```

## Output
- Real-time blockchain event streaming
- Custom filter functions for specific contracts/events
- Webhook delivery for processed events

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No events received | Filter too restrictive | Test with broader filter first |
| Duplicate events | Block reorganization | Implement idempotency by tx hash |
| Webhook timeout | Slow processing | Return 200 immediately, process async |

## Resources
- [QuickNode Streams](https://www.quicknode.com/docs/streams)
- [QuickNode Docs](https://www.quicknode.com/docs/welcome)

## Next Steps
Optimize performance: `quicknode-performance-tuning`
