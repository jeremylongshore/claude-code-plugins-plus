---
name: quicknode-install-auth
description: |
  QuickNode install auth — blockchain RPC and Web3 infrastructure integration.
  Use when working with QuickNode for blockchain development.
  Trigger with phrases like "quicknode install auth", "quicknode-install-auth", "blockchain RPC".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, quicknode, blockchain, web3, rpc, ethereum]
compatible-with: claude-code, codex, openclaw
---

# QuickNode Install Auth

## Overview
Set up QuickNode blockchain RPC endpoints and install the QuickNode SDK or ethers.js for blockchain interactions.

## Prerequisites
- QuickNode account at quicknode.com
- An endpoint created for your target chain (Ethereum, Solana, etc.)
- Node.js 18+

## Instructions

### Step 1: Create Endpoint
```text
1. Go to quicknode.com > Dashboard > Create Endpoint
2. Select chain: Ethereum Mainnet (or testnet for development)
3. Copy the HTTP URL and WSS URL
   HTTP: https://xxx-yyy.quiknode.pro/TOKEN/
   WSS: wss://xxx-yyy.quiknode.pro/TOKEN/
```

### Step 2: Install SDK
```bash
set -euo pipefail
npm install @quicknode/sdk viem
# Or with ethers.js
npm install ethers
```

### Step 3: Configure Environment
```bash
# .env
QUICKNODE_ENDPOINT=https://xxx-yyy.quiknode.pro/YOUR_TOKEN/
QUICKNODE_WSS=wss://xxx-yyy.quiknode.pro/YOUR_TOKEN/
```

### Step 4: Verify Connection (QuickNode SDK)
```typescript
import { Core } from '@quicknode/sdk';

const core = new Core({ endpointUrl: process.env.QUICKNODE_ENDPOINT });
const blockNumber = await core.client.request({ method: 'eth_blockNumber' });
console.log(`Connected! Current block: ${parseInt(blockNumber, 16)}`);
```

### Step 5: Verify Connection (ethers.js)
```typescript
import { ethers } from 'ethers';

const provider = new ethers.JsonRpcProvider(process.env.QUICKNODE_ENDPOINT);
const block = await provider.getBlockNumber();
console.log(`Connected! Block: ${block}`);
```

## Output
- QuickNode endpoint configured
- SDK installed and verified
- Successful RPC call confirming connectivity

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid token in URL | Verify endpoint URL from Dashboard |
| `ECONNREFUSED` | Wrong endpoint URL | Check HTTPS URL format |
| `eth method not found` | Add-on required | Enable add-on in QuickNode Dashboard |

## Resources
- [QuickNode SDK Getting Started](https://www.quicknode.com/docs/quicknode-sdk/getting-started)
- [Ethereum Quickstart](https://www.quicknode.com/docs/ethereum/quickstart)

## Next Steps
First blockchain query: `quicknode-hello-world`
