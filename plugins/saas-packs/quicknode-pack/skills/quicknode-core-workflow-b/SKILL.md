---
name: quicknode-core-workflow-b
description: |
  Work with NFT and token APIs via QuickNode: metadata, balances, transfer history.
  Use when building NFT or token features, checking balances, or tracking transfers.
  Trigger with phrases like "quicknode NFT", "token balance", "NFT metadata", "ERC-20 balance".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, quicknode, blockchain, nft, tokens, web3]
compatible-with: claude-code, codex, openclaw
---

# QuickNode Core Workflow B — NFT & Token APIs

## Overview
Use QuickNode's NFT and Token APIs to fetch metadata, check balances, and track transfer history. These are QuickNode-specific add-on APIs beyond standard EVM RPC.

## Prerequisites
- Completed `quicknode-core-workflow-a`
- Token and NFT add-ons enabled on your QuickNode endpoint

## Instructions

### Step 1: Get Token Balances (QuickNode SDK)
```typescript
import { Core } from '@quicknode/sdk';

const core = new Core({ endpointUrl: process.env.QUICKNODE_ENDPOINT });

// Get all ERC-20 token balances for a wallet
const balances = await core.client.request({
  method: 'qn_getWalletTokenBalance',
  params: [{ wallet: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045' }],
});
for (const token of balances.result) {
  console.log(`${token.name} (${token.symbol}): ${token.quantity}`);
}
```

### Step 2: Get NFT Metadata
```typescript
const nfts = await core.client.request({
  method: 'qn_fetchNFTs',
  params: [{
    wallet: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    contracts: ['0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D'],  // BAYC
    page: 1,
    perPage: 10,
  }],
});
for (const nft of nfts.result.assets) {
  console.log(`${nft.name} — Token ID: ${nft.tokenId}`);
  console.log(`  Image: ${nft.imageUrl}`);
}
```

### Step 3: Track ERC-20 Transfers
```typescript
const transfers = await core.client.request({
  method: 'qn_getWalletTokenTransactions',
  params: [{
    address: '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045',
    contract: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',  // USDC
    page: 1,
    perPage: 10,
  }],
});
for (const tx of transfers.result.transfers) {
  console.log(`${tx.from} -> ${tx.to}: ${tx.value} at block ${tx.blockNumber}`);
}
```

### Step 4: Standard ERC-20 Balance (No Add-on Required)
```typescript
import { ethers } from 'ethers';

const provider = new ethers.JsonRpcProvider(process.env.QUICKNODE_ENDPOINT);
const erc20Abi = ['function balanceOf(address) view returns (uint256)', 'function decimals() view returns (uint8)', 'function symbol() view returns (string)'];
const token = new ethers.Contract('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', erc20Abi, provider);

const [balance, decimals, symbol] = await Promise.all([
  token.balanceOf('0xWalletAddress'),
  token.decimals(),
  token.symbol(),
]);
console.log(`${symbol} balance: ${ethers.formatUnits(balance, decimals)}`);
```

## Output
- ERC-20 token balances for any wallet
- NFT metadata with images and attributes
- Transfer history for token tracking
- Direct contract reads for standard operations

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Method not found: qn_*` | Add-on not enabled | Enable in QuickNode Dashboard |
| Empty results | No tokens at address | Verify address is correct |
| `call revert` on balanceOf | Wrong contract address | Verify ERC-20 contract |

## Resources
- [QuickNode Token API](https://www.quicknode.com/docs/ethereum)
- [QuickNode NFT API](https://www.quicknode.com/docs/ethereum)
- [ERC-20 Token Guide](https://www.quicknode.com/guides/ethereum-development/transactions/how-to-send-erc20-tokens-using-qn-sdk)

## Next Steps
Handle errors: `quicknode-common-errors`
