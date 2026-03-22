---
name: alchemy-hello-world
description: |
  Create a minimal Alchemy Web3 example: get ETH balance, fetch NFTs, read token balances.
  Use when starting blockchain development, testing Alchemy setup,
  or learning basic blockchain query patterns.
  Trigger: "alchemy hello world", "alchemy example", "alchemy quick start",
  "get ETH balance", "fetch NFTs alchemy".
allowed-tools: Read, Write, Edit, Bash(npm:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, nft]
compatible-with: claude-code
---

# Alchemy Hello World

## Overview

Minimal working examples with the real Alchemy SDK: get ETH balance, fetch NFTs for a wallet, read ERC-20 token balances, and subscribe to pending transactions.

## Prerequisites

- Completed `alchemy-install-auth` setup
- `alchemy-sdk` installed (`npm install alchemy-sdk`)
- Valid API key configured

## Instructions

### Step 1: Get ETH Balance

```typescript
// src/hello-world/get-balance.ts
import { Alchemy, Network, Utils } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function getBalance(address: string) {
  const balanceWei = await alchemy.core.getBalance(address);
  const balanceEth = Utils.formatEther(balanceWei);
  console.log(`Balance of ${address}: ${balanceEth} ETH`);
  return balanceEth;
}

// Query Vitalik's address
getBalance('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045').catch(console.error);
```

### Step 2: Fetch NFTs for a Wallet

```typescript
// src/hello-world/get-nfts.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function getNftsForOwner(owner: string) {
  const nfts = await alchemy.nft.getNftsForOwner(owner);
  console.log(`Total NFTs: ${nfts.totalCount}`);

  for (const nft of nfts.ownedNfts.slice(0, 5)) {
    console.log(`  ${nft.contract.name} — ${nft.name || nft.tokenId}`);
    console.log(`    Contract: ${nft.contract.address}`);
    console.log(`    Token ID: ${nft.tokenId}`);
    if (nft.image?.cachedUrl) {
      console.log(`    Image: ${nft.image.cachedUrl}`);
    }
  }

  return nfts;
}

getNftsForOwner('vitalik.eth').catch(console.error);
```

### Step 3: Get ERC-20 Token Balances

```typescript
// src/hello-world/get-tokens.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function getTokenBalances(address: string) {
  const balances = await alchemy.core.getTokenBalances(address);

  console.log(`Token balances for ${address}:`);
  for (const token of balances.tokenBalances.slice(0, 10)) {
    if (token.tokenBalance && token.tokenBalance !== '0x0') {
      // Get token metadata for human-readable names
      const metadata = await alchemy.core.getTokenMetadata(token.contractAddress);
      const balance = parseInt(token.tokenBalance, 16) / Math.pow(10, metadata.decimals || 18);
      console.log(`  ${metadata.symbol}: ${balance.toFixed(4)}`);
    }
  }
}

getTokenBalances('0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045').catch(console.error);
```

### Step 4: Get Latest Block Info

```typescript
// src/hello-world/get-block.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function getLatestBlock() {
  const blockNumber = await alchemy.core.getBlockNumber();
  const block = await alchemy.core.getBlock(blockNumber);

  console.log(`Block #${blockNumber}`);
  console.log(`  Hash: ${block.hash}`);
  console.log(`  Timestamp: ${new Date(block.timestamp * 1000).toISOString()}`);
  console.log(`  Transactions: ${block.transactions.length}`);
  console.log(`  Gas Used: ${block.gasUsed.toString()}`);
}

getLatestBlock().catch(console.error);
```

## Output

- ETH balance query with Wei → ETH conversion
- NFT enumeration with metadata and images
- ERC-20 token balances with symbol resolution
- Block data with timestamp and gas usage

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid address` | Malformed Ethereum address | Use checksummed 0x-prefixed address |
| `429 Too Many Requests` | Rate limit exceeded | Add delay between calls or upgrade plan |
| `ENS name not found` | ENS not resolving | Verify ENS name exists on mainnet |
| Timeout | Slow node response | Increase timeout in SDK config |

## Resources

- [Alchemy SDK Reference](https://www.alchemy.com/docs/reference/sdk-getbalance)
- [Alchemy NFT API](https://www.alchemy.com/docs/reference/nft-api-quickstart)
- [Alchemy Enhanced APIs](https://www.alchemy.com/docs)

## Next Steps

Proceed to `alchemy-local-dev-loop` for development workflow setup.
