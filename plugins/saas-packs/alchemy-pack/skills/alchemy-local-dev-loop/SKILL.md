---
name: alchemy-local-dev-loop
description: |
  Set up local Web3 development workflow with Alchemy, Hardhat, and testnets.
  Use when configuring local blockchain dev, testing with Sepolia faucets,
  or setting up hot-reload for smart contract development.
  Trigger: "alchemy local dev", "alchemy hardhat", "alchemy testnet setup".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, development]
compatible-with: claude-code
---

# Alchemy Local Dev Loop

## Overview

Local Web3 development workflow using Alchemy as the RPC provider with Hardhat for local testing, Sepolia testnet for staging, and hot-reload for rapid iteration.

## Prerequisites

- Completed `alchemy-install-auth` setup
- Node.js 18+
- Alchemy API key with Sepolia testnet app

## Instructions

### Step 1: Initialize Hardhat Project with Alchemy

```bash
mkdir web3-project && cd web3-project
npm init -y
npm install --save-dev hardhat @nomicfoundation/hardhat-toolbox
npm install alchemy-sdk dotenv
npx hardhat init  # Select TypeScript project
```

### Step 2: Configure Hardhat with Alchemy RPC

```typescript
// hardhat.config.ts
import { HardhatUserConfig } from 'hardhat/config';
import '@nomicfoundation/hardhat-toolbox';
import 'dotenv/config';

const config: HardhatUserConfig = {
  solidity: '0.8.24',
  networks: {
    hardhat: {
      forking: {
        url: `https://eth-mainnet.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
        blockNumber: 19000000,  // Pin block for reproducible tests
      },
    },
    sepolia: {
      url: `https://eth-sepolia.g.alchemy.com/v2/${process.env.ALCHEMY_API_KEY}`,
      accounts: process.env.DEPLOYER_PRIVATE_KEY ? [process.env.DEPLOYER_PRIVATE_KEY] : [],
    },
  },
};

export default config;
```

### Step 3: Alchemy-Powered Test Helper

```typescript
// test/helpers/alchemy-helper.ts
import { Alchemy, Network } from 'alchemy-sdk';

const alchemy = new Alchemy({
  apiKey: process.env.ALCHEMY_API_KEY,
  network: Network.ETH_SEPOLIA,
});

export async function getTestnetBalance(address: string): Promise<string> {
  const balance = await alchemy.core.getBalance(address);
  return (parseInt(balance.toString()) / 1e18).toFixed(4);
}

export async function waitForTransaction(txHash: string): Promise<any> {
  return alchemy.core.waitForTransaction(txHash, 1, 60000);
}

export { alchemy };
```

### Step 4: Development Scripts

```json
{
  "scripts": {
    "dev": "npx hardhat node --fork https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}",
    "test": "npx hardhat test",
    "test:watch": "npx hardhat test --watch",
    "deploy:sepolia": "npx hardhat run scripts/deploy.ts --network sepolia",
    "verify": "npx hardhat verify --network sepolia"
  }
}
```

### Step 5: Mainnet Fork Testing

```typescript
// test/fork-test.ts
import { expect } from 'chai';
import { ethers } from 'hardhat';

describe('Mainnet Fork Tests', () => {
  it('should read USDC balance on forked mainnet', async () => {
    const USDC = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';
    const usdc = await ethers.getContractAt('IERC20', USDC);
    const totalSupply = await usdc.totalSupply();
    expect(totalSupply).to.be.gt(0);
  });

  it('should impersonate whale account', async () => {
    const whale = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045';
    await ethers.provider.send('hardhat_impersonateAccount', [whale]);
    const signer = await ethers.getSigner(whale);
    const balance = await ethers.provider.getBalance(whale);
    expect(balance).to.be.gt(0);
  });
});
```

## Output

- Hardhat project with Alchemy RPC (mainnet fork + Sepolia)
- Alchemy-powered test helpers for balance checks and tx waiting
- Mainnet fork testing with account impersonation
- Development scripts with watch mode

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Fork timeout | Alchemy rate limit | Pin block number; upgrade plan |
| `ProviderError: missing trie node` | Stale fork block | Use more recent block number |
| Sepolia deploy fails | Insufficient test ETH | Get from Alchemy Sepolia faucet |
| `nonce too low` | Stale nonce cache | Reset Hardhat network or clear nonce |

## Resources

- [Hardhat Alchemy Guide](https://hardhat.org/hardhat-runner/docs/guides/forking-other-networks)
- [Alchemy Sepolia Faucet](https://sepoliafaucet.com)
- [Alchemy Docs](https://www.alchemy.com/docs)

## Next Steps

For SDK patterns and best practices, see `alchemy-sdk-patterns`.
