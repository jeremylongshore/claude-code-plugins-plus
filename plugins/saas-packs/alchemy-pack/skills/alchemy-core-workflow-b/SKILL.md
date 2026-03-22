---
name: alchemy-core-workflow-b
description: |
  Build NFT collection explorer and smart contract interaction with Alchemy.
  Use when fetching NFT metadata, building galleries, reading contract state,
  or implementing NFT marketplace features.
  Trigger: "alchemy NFT", "alchemy smart contract", "alchemy collection",
  "alchemy NFT metadata", "alchemy contract read".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, nft, smart-contracts]
compatible-with: claude-code
---

# Alchemy Core Workflow B — NFT & Smart Contract Interaction

## Overview

Build NFT collection explorers and smart contract read operations using Alchemy's NFT API and core JSON-RPC methods.

## Prerequisites

- Completed `alchemy-install-auth` setup
- Familiarity with `alchemy-core-workflow-a`
- Understanding of ERC-721 and ERC-1155 standards

## Instructions

### Step 1: NFT Collection Explorer

```typescript
// src/nft/collection-explorer.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function exploreCollection(contractAddress: string) {
  const metadata = await alchemy.nft.getContractMetadata(contractAddress);

  return {
    address: contractAddress,
    name: metadata.name || 'Unknown',
    symbol: metadata.symbol || '',
    totalSupply: metadata.totalSupply || '0',
    tokenType: metadata.tokenType,
    floorPrice: metadata.openSeaMetadata?.floorPrice || null,
    description: metadata.openSeaMetadata?.description || '',
    imageUrl: metadata.openSeaMetadata?.imageUrl || null,
  };
}

async function getCollectionNfts(contractAddress: string, limit: number = 20) {
  const response = await alchemy.nft.getNftsForContract(contractAddress, { limit });
  return response.nfts.map(nft => ({
    tokenId: nft.tokenId,
    name: nft.name || `#${nft.tokenId}`,
    description: nft.description,
    image: nft.image?.cachedUrl || nft.image?.originalUrl,
    attributes: nft.raw?.metadata?.attributes || [],
  }));
}

// Example: Bored Ape Yacht Club
const BAYC = '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D';
exploreCollection(BAYC).then(console.log).catch(console.error);
```

### Step 2: Batch NFT Metadata

```typescript
// src/nft/batch-metadata.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function batchGetNftMetadata(
  tokens: Array<{ contractAddress: string; tokenId: string }>
) {
  const results = await alchemy.nft.getNftMetadataBatch(
    tokens.map(t => ({ contractAddress: t.contractAddress, tokenId: t.tokenId }))
  );
  return results.map(nft => ({
    contract: nft.contract.address,
    tokenId: nft.tokenId,
    name: nft.name,
    image: nft.image?.cachedUrl,
    tokenType: nft.tokenType,
    collection: nft.contract.name,
  }));
}
```

### Step 3: Smart Contract Read via Ethers + Alchemy Provider

```typescript
// src/contracts/read-contract.ts
import { Alchemy, Network } from 'alchemy-sdk';
import { ethers } from 'ethers';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function readErc20Contract(contractAddress: string) {
  const provider = await alchemy.config.getProvider();
  const erc20Abi = [
    'function name() view returns (string)',
    'function symbol() view returns (string)',
    'function decimals() view returns (uint8)',
    'function totalSupply() view returns (uint256)',
    'function balanceOf(address) view returns (uint256)',
  ];

  const contract = new ethers.Contract(contractAddress, erc20Abi, provider);
  const [name, symbol, decimals, totalSupply] = await Promise.all([
    contract.name(), contract.symbol(), contract.decimals(), contract.totalSupply(),
  ]);

  return { address: contractAddress, name, symbol, decimals, totalSupply: ethers.formatUnits(totalSupply, decimals) };
}

// Example: Read USDC contract
readErc20Contract('0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48').then(console.log);
```

### Step 4: NFT Ownership Verification

```typescript
// src/nft/verify-ownership.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_MAINNET,
});

async function verifyNftOwnership(
  ownerAddress: string,
  contractAddress: string,
  tokenId?: string,
): Promise<boolean> {
  if (tokenId) {
    const owners = await alchemy.nft.getOwnersForNft(contractAddress, tokenId);
    return owners.owners.some(o => o.toLowerCase() === ownerAddress.toLowerCase());
  }
  const nfts = await alchemy.nft.getNftsForOwner(ownerAddress, {
    contractAddresses: [contractAddress],
  });
  return nfts.totalCount > 0;
}
```

## Output

- NFT collection explorer with OpenSea metadata and floor price
- Batch metadata fetching for gallery views
- Smart contract read operations via Ethers.js provider
- NFT ownership verification for token-gating

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Contract not found` | Wrong address or chain | Verify contract on correct network |
| `call revert exception` | ABI mismatch | Verify contract implements the interface |
| Rate limit on batch | Too many requests | Reduce batch size; add delay |
| Empty NFT images | IPFS timeout | Use Alchemy's `cachedUrl` field |

## Resources

- [Alchemy NFT API](https://www.alchemy.com/docs/reference/nft-api-quickstart)
- [Alchemy SDK GitHub](https://github.com/alchemyplatform/alchemy-sdk-js)
- [Ethers.js v6](https://docs.ethers.org/v6/)

## Next Steps

For common errors and debugging, see `alchemy-common-errors`.
