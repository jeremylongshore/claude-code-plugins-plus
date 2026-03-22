---
name: quicknode-hello-world
description: |
  QuickNode hello world — blockchain RPC and Web3 infrastructure integration.
  Use when working with QuickNode for blockchain development.
  Trigger with phrases like "quicknode hello world", "quicknode-hello-world", "blockchain RPC".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, quicknode, blockchain, web3, rpc, ethereum]
compatible-with: claude-code, codex, openclaw
---

# QuickNode Hello World

## Overview
Make your first blockchain queries: get block number, check ETH balance, read a smart contract.

## Prerequisites
- Completed `quicknode-install-auth` with endpoint URL

## Instructions

### Step 1: Get Block Number
```typescript
import { ethers } from 'ethers';
const provider = new ethers.JsonRpcProvider(process.env.QUICKNODE_ENDPOINT);

const blockNumber = await provider.getBlockNumber();
console.log(`Current block: ${blockNumber}`);
```

### Step 2: Check ETH Balance
```typescript
const address = '0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045'; // vitalik.eth
const balance = await provider.getBalance(address);
console.log(`Balance: ${ethers.formatEther(balance)} ETH`);
```

### Step 3: Read Smart Contract (ERC-20 Token)
```typescript
const usdcAddress = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48';
const abi = ['function balanceOf(address) view returns (uint256)', 'function decimals() view returns (uint8)'];
const usdc = new ethers.Contract(usdcAddress, abi, provider);

const decimals = await usdc.decimals();
const balance = await usdc.balanceOf(address);
console.log(`USDC balance: ${ethers.formatUnits(balance, decimals)}`);
```

### Step 4: Get Transaction Receipt
```typescript
const txHash = '0xabc...'; // Any transaction hash
const receipt = await provider.getTransactionReceipt(txHash);
console.log(`Status: ${receipt?.status === 1 ? 'Success' : 'Failed'}`);
console.log(`Gas used: ${receipt?.gasUsed.toString()}`);
```

## Output
- Block number retrieved
- ETH balance checked
- ERC-20 contract read
- Transaction receipt fetched

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `null` receipt | TX pending or invalid hash | Wait for confirmation or verify hash |
| `call revert exception` | Wrong ABI or address | Verify contract address and ABI |
| Balance is 0n | Address has no ETH | Try a known address like vitalik.eth |

## Resources
- [QuickNode Ethereum API](https://www.quicknode.com/docs/ethereum)
- [ethers.js Documentation](https://docs.ethers.org/)

## Next Steps
Build transaction workflows: `quicknode-core-workflow-a`
