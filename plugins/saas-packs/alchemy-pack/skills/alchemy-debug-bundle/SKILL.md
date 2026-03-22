---
name: alchemy-debug-bundle
description: |
  Collect Alchemy SDK debug evidence for troubleshooting and support tickets.
  Use when encountering persistent issues, preparing support tickets,
  or debugging blockchain query failures.
  Trigger: "alchemy debug bundle", "alchemy support ticket", "alchemy diagnostics".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, debugging]
compatible-with: claude-code
---

# Alchemy Debug Bundle

## Overview

Collect diagnostic data for Alchemy support tickets: connectivity tests, SDK version, network status, CU usage, and recent error logs.

## Instructions

### Step 1: Debug Bundle Generator

```typescript
// src/debug/alchemy-debug.ts
import { Alchemy, Network } from 'alchemy-sdk';

interface DebugBundle {
  timestamp: string;
  sdkVersion: string;
  environment: Record<string, string>;
  connectivity: Record<string, any>;
  networkStatus: Record<string, any>;
}

async function generateDebugBundle(): Promise<DebugBundle> {
  const alchemy = new Alchemy({
    apiKey: process.env.ALCHEMY_API_KEY,
    network: Network.ETH_MAINNET,
  });

  const bundle: DebugBundle = {
    timestamp: new Date().toISOString(),
    sdkVersion: require('alchemy-sdk/package.json').version,
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      apiKeySet: process.env.ALCHEMY_API_KEY ? 'yes (redacted)' : 'NO — missing',
      network: process.env.ALCHEMY_NETWORK || 'ETH_MAINNET',
    },
    connectivity: {},
    networkStatus: {},
  };

  // Test core connectivity
  try {
    const start = Date.now();
    const blockNumber = await alchemy.core.getBlockNumber();
    bundle.connectivity.core = {
      status: 'ok',
      latencyMs: Date.now() - start,
      latestBlock: blockNumber,
    };
  } catch (err: any) {
    bundle.connectivity.core = { status: 'failed', error: err.message };
  }

  // Test Enhanced API
  try {
    const start = Date.now();
    await alchemy.core.getTokenBalances('0x0000000000000000000000000000000000000000');
    bundle.connectivity.enhancedApi = { status: 'ok', latencyMs: Date.now() - start };
  } catch (err: any) {
    bundle.connectivity.enhancedApi = { status: 'failed', error: err.message };
  }

  // Test NFT API
  try {
    const start = Date.now();
    await alchemy.nft.getContractMetadata('0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D');
    bundle.connectivity.nftApi = { status: 'ok', latencyMs: Date.now() - start };
  } catch (err: any) {
    bundle.connectivity.nftApi = { status: 'failed', error: err.message };
  }

  // Multi-network status
  for (const [name, network] of Object.entries({
    ethereum: Network.ETH_MAINNET,
    polygon: Network.MATIC_MAINNET,
    arbitrum: Network.ARB_MAINNET,
  })) {
    try {
      const client = new Alchemy({ apiKey: process.env.ALCHEMY_API_KEY, network });
      const block = await client.core.getBlockNumber();
      bundle.networkStatus[name] = { status: 'ok', block };
    } catch (err: any) {
      bundle.networkStatus[name] = { status: 'failed', error: err.message };
    }
  }

  const filename = `alchemy-debug-${Date.now()}.json`;
  require('fs').writeFileSync(filename, JSON.stringify(bundle, null, 2));
  console.log(`Debug bundle saved: ${filename}`);
  return bundle;
}

generateDebugBundle().catch(console.error);
```

### Step 2: Bash Quick Diagnostic

```bash
#!/bin/bash
echo "=== Alchemy Quick Diagnostics ==="
echo "API Key: ${ALCHEMY_API_KEY:+SET (redacted)}"

echo -n "ETH Mainnet: "
curl -s "https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}" \
  -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":0}' \
  | jq -r '.result // .error.message'

echo -n "Polygon: "
curl -s "https://polygon-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}" \
  -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":0}' \
  | jq -r '.result // .error.message'

echo "=== Done ==="
```

## Output

- JSON debug bundle with connectivity, latency, and network status
- SDK version and environment configuration
- Multi-network health check results

## Resources

- [Alchemy Status Page](https://status.alchemy.com)
- [Alchemy Support](https://www.alchemy.com/support)

## Next Steps

For rate limit handling, see `alchemy-rate-limits`.
