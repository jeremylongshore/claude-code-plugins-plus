---
name: alchemy-core-workflow-a
description: |
  Build a complete wallet portfolio tracker using Alchemy Enhanced APIs.
  Use when implementing token balance dashboards, NFT galleries,
  transaction history views, or wallet analytics applications.
  Trigger: "alchemy wallet tracker", "alchemy portfolio", "alchemy token dashboard",
  "alchemy transaction history", "build dApp with alchemy".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, defi, portfolio]
compatible-with: claude-code
---

# Alchemy Core Workflow A — Wallet Portfolio Tracker

## Overview

Primary workflow: build a wallet portfolio tracker using Alchemy's Enhanced APIs. Combines `getTokenBalances`, `getNftsForOwner`, `getAssetTransfers`, and token metadata to create a complete wallet view across ERC-20, ERC-721, and ERC-1155 assets.

## Prerequisites

- Completed `alchemy-install-auth` setup
- `alchemy-sdk` installed
- Understanding of Ethereum address format and token standards

## Instructions

### Step 1: Portfolio Data Fetcher

```typescript
// src/portfolio/fetcher.ts
import { Alchemy, Network, AssetTransfersCategory } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

interface TokenHolding {
  contractAddress: string;
  symbol: string;
  name: string;
  balance: number;
  decimals: number;
}

interface NftHolding {
  contractAddress: string;
  collectionName: string;
  tokenId: string;
  name: string;
  imageUrl: string | null;
}

interface WalletPortfolio {
  address: string;
  ethBalance: string;
  tokens: TokenHolding[];
  nfts: NftHolding[];
  recentTransactions: any[];
  fetchedAt: string;
}

async function fetchPortfolio(address: string): Promise<WalletPortfolio> {
  // Parallel fetch all portfolio data
  const [ethBalance, tokenBalances, nftResponse, transfers] = await Promise.all([
    alchemy.core.getBalance(address),
    alchemy.core.getTokenBalances(address),
    alchemy.nft.getNftsForOwner(address, { pageSize: 100 }),
    alchemy.core.getAssetTransfers({
      fromAddress: address,
      category: [
        AssetTransfersCategory.EXTERNAL,
        AssetTransfersCategory.ERC20,
        AssetTransfersCategory.ERC721,
      ],
      maxCount: 25,
      order: 'desc',
    }),
  ]);

  // Resolve token metadata
  const tokens: TokenHolding[] = [];
  for (const tb of tokenBalances.tokenBalances) {
    if (tb.tokenBalance && tb.tokenBalance !== '0x0') {
      const metadata = await alchemy.core.getTokenMetadata(tb.contractAddress);
      const balance = parseInt(tb.tokenBalance, 16) / Math.pow(10, metadata.decimals || 18);
      if (balance > 0.001) {  // Filter dust
        tokens.push({
          contractAddress: tb.contractAddress,
          symbol: metadata.symbol || 'UNKNOWN',
          name: metadata.name || 'Unknown Token',
          balance,
          decimals: metadata.decimals || 18,
        });
      }
    }
  }

  // Map NFTs
  const nfts: NftHolding[] = nftResponse.ownedNfts.map(nft => ({
    contractAddress: nft.contract.address,
    collectionName: nft.contract.name || 'Unknown Collection',
    tokenId: nft.tokenId,
    name: nft.name || `#${nft.tokenId}`,
    imageUrl: nft.image?.cachedUrl || null,
  }));

  return {
    address,
    ethBalance: (parseInt(ethBalance.toString()) / 1e18).toFixed(6),
    tokens: tokens.sort((a, b) => b.balance - a.balance),
    nfts,
    recentTransactions: transfers.transfers,
    fetchedAt: new Date().toISOString(),
  };
}

export { fetchPortfolio, WalletPortfolio };
```

### Step 2: Transaction History Analyzer

```typescript
// src/portfolio/transactions.ts
import { Alchemy, Network, AssetTransfersCategory, SortingOrder } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function getTransactionHistory(address: string, maxCount: number = 50) {
  // Get both sent and received transactions
  const [sent, received] = await Promise.all([
    alchemy.core.getAssetTransfers({
      fromAddress: address,
      category: [AssetTransfersCategory.EXTERNAL, AssetTransfersCategory.ERC20],
      maxCount,
      order: 'desc',
    }),
    alchemy.core.getAssetTransfers({
      toAddress: address,
      category: [AssetTransfersCategory.EXTERNAL, AssetTransfersCategory.ERC20],
      maxCount,
      order: 'desc',
    }),
  ]);

  // Merge and sort by block number
  const allTransfers = [
    ...sent.transfers.map(t => ({ ...t, direction: 'sent' as const })),
    ...received.transfers.map(t => ({ ...t, direction: 'received' as const })),
  ].sort((a, b) => parseInt(b.blockNum) - parseInt(a.blockNum));

  return allTransfers;
}

export { getTransactionHistory };
```

### Step 3: Multi-Chain Portfolio Aggregator

```typescript
// src/portfolio/multi-chain.ts
import { Alchemy, Network } from 'alchemy-sdk';

const CHAINS = [
  { name: 'Ethereum', network: Network.ETH_MAINNET },
  { name: 'Polygon', network: Network.MATIC_MAINNET },
  { name: 'Arbitrum', network: Network.ARB_MAINNET },
  { name: 'Optimism', network: Network.OPT_MAINNET },
  { name: 'Base', network: Network.BASE_MAINNET },
];

async function getMultiChainBalances(address: string) {
  const results = await Promise.allSettled(
    CHAINS.map(async (chain) => {
      const client = new Alchemy({
        apiKey: process.env.ALCHEMY_API_KEY,
        network: chain.network,
      });
      const balance = await client.core.getBalance(address);
      const tokens = await client.core.getTokenBalances(address);
      const nonZeroTokens = tokens.tokenBalances.filter(
        t => t.tokenBalance && t.tokenBalance !== '0x0'
      );
      return {
        chain: chain.name,
        nativeBalance: (parseInt(balance.toString()) / 1e18).toFixed(6),
        tokenCount: nonZeroTokens.length,
      };
    })
  );

  return results
    .filter((r): r is PromiseFulfilledResult<any> => r.status === 'fulfilled')
    .map(r => r.value);
}

export { getMultiChainBalances };
```

## Output

- Complete wallet portfolio: ETH + ERC-20 tokens + NFTs
- Transaction history with sent/received classification
- Multi-chain balance aggregation across 5 networks
- Sorted holdings with dust filtering

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `429 Rate Limit` | Too many metadata calls | Batch with delays or cache metadata |
| Empty token list | Address has no tokens | Verify address is correct |
| Missing NFT images | IPFS gateway timeout | Use Alchemy's cached URL fallback |
| `getAssetTransfers` empty | Wrong category filter | Include all relevant categories |

## Resources

- [Alchemy Enhanced APIs](https://www.alchemy.com/docs)
- [Alchemy NFT API](https://www.alchemy.com/docs/reference/nft-api-quickstart)
- [Alchemy Asset Transfers](https://www.alchemy.com/docs/reference/sdk-getassettransfers)

## Next Steps

For NFT minting and smart contract interaction, see `alchemy-core-workflow-b`.
