---
name: alchemy-upgrade-migration
description: |
  Migrate from alchemy-sdk v2 to v3 and handle breaking changes.
  Use when upgrading Alchemy SDK versions, migrating from deprecated
  alchemy-web3, or adapting to new API patterns.
  Trigger: "alchemy upgrade", "alchemy migration", "alchemy-sdk v3",
  "migrate alchemy-web3", "alchemy breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, migration]
compatible-with: claude-code
---

# Alchemy Upgrade & Migration

## Overview

Migration guide for Alchemy SDK upgrades and deprecated package transitions. The `alchemy-web3` package is deprecated — migrate to `alchemy-sdk`.

## Migration Paths

| From | To | Complexity |
|------|----|-----------|
| `alchemy-web3` | `alchemy-sdk` | High (different API surface) |
| `alchemy-sdk` v2 → v3 | `alchemy-sdk` v3 | Medium (some breaking changes) |
| Direct JSON-RPC | `alchemy-sdk` | Low (SDK wraps same methods) |

## Instructions

### Step 1: Migrate from alchemy-web3 to alchemy-sdk

```typescript
// BEFORE: alchemy-web3 (DEPRECATED)
// import { createAlchemyWeb3 } from '@alch/alchemy-web3';
// const web3 = createAlchemyWeb3(`https://eth-mainnet.g.alchemy.com/v2/${apiKey}`);
// const balance = await web3.eth.getBalance(address);
// const nfts = await web3.alchemy.getNfts({ owner });

// AFTER: alchemy-sdk
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

// Core methods — same JSON-RPC, different API
const balance = await alchemy.core.getBalance(address);

// Enhanced APIs — reorganized under namespaces
const nfts = await alchemy.nft.getNftsForOwner(owner);

// WebSockets — now under alchemy.ws
alchemy.ws.on({ method: 'eth_subscribe', params: ['newHeads'] }, (block) => {
  console.log('New block:', block);
});
```

### Step 2: API Surface Changes

```typescript
// Key namespace changes in alchemy-sdk:

// Core (JSON-RPC wrapper)
alchemy.core.getBlockNumber();
alchemy.core.getBalance(address);
alchemy.core.getTokenBalances(address);
alchemy.core.getTokenMetadata(contractAddress);
alchemy.core.getAssetTransfers({ fromAddress, category });

// NFT (dedicated namespace)
alchemy.nft.getNftsForOwner(owner);
alchemy.nft.getNftsForContract(contract);
alchemy.nft.getContractMetadata(contract);
alchemy.nft.getNftMetadataBatch(tokens);
alchemy.nft.getOwnersForNft(contract, tokenId);

// WebSocket (real-time)
alchemy.ws.on(filter, callback);
alchemy.ws.once(filter, callback);
alchemy.ws.removeAllListeners();

// Notify (webhooks — requires authToken)
alchemy.notify.getAllWebhooks();
alchemy.notify.createWebhook(config);
```

### Step 3: Dependency Cleanup

```bash
# Remove deprecated packages
npm uninstall @alch/alchemy-web3 alchemy-web3

# Install current SDK
npm install alchemy-sdk

# Check for leftover imports
grep -rn "alchemy-web3\|@alch/alchemy" src/ --include='*.ts' --include='*.js'

# Update ethers if needed (alchemy-sdk works with ethers v5 and v6)
npm install ethers@6
```

### Step 4: Test Migration

```typescript
// tests/migration.test.ts
import { describe, it, expect } from 'vitest';
import { Alchemy, Network } from 'alchemy-sdk';

describe('Alchemy SDK Migration', () => {
  const alchemy = new Alchemy({
    apiKey: process.env.ALCHEMY_API_KEY,
    network: Network.ETH_SEPOLIA,
  });

  it('should get block number via core namespace', async () => {
    const block = await alchemy.core.getBlockNumber();
    expect(block).toBeGreaterThan(0);
  });

  it('should get NFTs via nft namespace', async () => {
    const nfts = await alchemy.nft.getNftsForOwner('0x0000000000000000000000000000000000000000');
    expect(nfts.totalCount).toBeDefined();
  });
});
```

## Output

- Migrated from `alchemy-web3` to `alchemy-sdk`
- All namespace changes applied (core, nft, ws, notify)
- Deprecated packages removed
- Migration tests passing

## Resources

- [Alchemy SDK Migration Guide](https://www.alchemy.com/docs)
- [alchemy-sdk npm](https://www.npmjs.com/package/alchemy-sdk)
- [alchemy-sdk GitHub](https://github.com/alchemyplatform/alchemy-sdk-js)

## Next Steps

For CI/CD setup, see `alchemy-ci-integration`.
