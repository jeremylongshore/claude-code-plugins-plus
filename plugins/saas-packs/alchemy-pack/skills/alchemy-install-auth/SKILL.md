---
name: alchemy-install-auth
description: |
  Install the Alchemy SDK and configure API key authentication for Web3 development.
  Use when setting up blockchain API access, creating an Alchemy app,
  or configuring multi-chain RPC endpoints.
  Trigger: "install alchemy", "setup alchemy", "alchemy auth", "alchemy API key".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy]
compatible-with: claude-code
---

# Alchemy Install & Auth

## Overview

Install the `alchemy-sdk` npm package and configure API authentication. Alchemy provides blockchain infrastructure (RPC nodes, Enhanced APIs, NFT APIs, webhooks) across Ethereum, Polygon, Arbitrum, Optimism, Base, and Solana.

## Prerequisites

- Node.js 18+ (or Python 3.10+ for alchemy-sdk Python)
- Free Alchemy account at [alchemy.com](https://www.alchemy.com)
- API key from Alchemy Dashboard

## Instructions

### Step 1: Install the Alchemy SDK

```bash
# JavaScript/TypeScript (official SDK)
npm install alchemy-sdk

# Python (community SDK)
pip install alchemy-sdk
```

### Step 2: Create an Alchemy App

1. Go to [dashboard.alchemy.com](https://dashboard.alchemy.com)
2. Click "Create new app"
3. Select chain: Ethereum, Polygon, Arbitrum, Optimism, Base, or Solana
4. Select network: Mainnet, Sepolia (testnet), or Mumbai
5. Copy the API key

### Step 3: Configure Environment

```bash
# Set environment variable
export ALCHEMY_API_KEY="your-api-key-here"

# Or create .env file
cat > .env << 'EOF'
ALCHEMY_API_KEY=your-api-key-here
ALCHEMY_NETWORK=ETH_MAINNET
EOF

echo ".env" >> .gitignore
```

### Step 4: Initialize and Verify

```typescript
// src/alchemy-client.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

// Verify connection
async function verifyConnection() {
  const blockNumber = await alchemy.core.getBlockNumber();
  console.log(`Connected! Latest block: ${blockNumber}`);
  return blockNumber;
}

verifyConnection().catch(console.error);
```

### Step 5: Multi-Chain Configuration

```typescript
// src/config/chains.ts
import { Alchemy, Network } from 'alchemy-sdk';

// Create clients for multiple chains
const chains = {
  ethereum: new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.ETH_MAINNET }),
  polygon: new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.MATIC_MAINNET }),
  arbitrum: new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.ARB_MAINNET }),
  optimism: new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.OPT_MAINNET }),
  base: new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network: Network.BASE_MAINNET }),
};

export default chains;
```

## Supported Networks

| Chain | Network Enum | Mainnet | Testnet |
|-------|-------------|---------|---------|
| Ethereum | `ETH_MAINNET` | Yes | Sepolia |
| Polygon | `MATIC_MAINNET` | Yes | Amoy |
| Arbitrum | `ARB_MAINNET` | Yes | Sepolia |
| Optimism | `OPT_MAINNET` | Yes | Sepolia |
| Base | `BASE_MAINNET` | Yes | Sepolia |
| Solana | `SOL_MAINNET` | Yes | Devnet |

## Output

- `alchemy-sdk` installed in node_modules
- API key configured in environment
- Verified connection with latest block number
- Multi-chain client configuration ready

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Must provide apiKey` | Missing env var | Set `ALCHEMY_API_KEY` in environment |
| `401 Unauthorized` | Invalid API key | Verify key in Alchemy Dashboard |
| `429 Rate Limit` | Free tier exceeded | Upgrade plan or reduce request rate |
| `ECONNREFUSED` | Network blocked | Ensure HTTPS to *.g.alchemy.com allowed |

## Resources

- [Alchemy Docs](https://www.alchemy.com/docs)
- [Alchemy SDK GitHub](https://github.com/alchemyplatform/alchemy-sdk-js)
- [Alchemy Dashboard](https://dashboard.alchemy.com)

## Next Steps

Proceed to `alchemy-hello-world` for your first blockchain query.
