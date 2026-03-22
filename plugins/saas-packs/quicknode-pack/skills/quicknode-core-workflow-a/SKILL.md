---
name: quicknode-core-workflow-a
description: |
  QuickNode core workflow a — blockchain RPC and Web3 infrastructure integration.
  Use when working with QuickNode for blockchain development.
  Trigger with phrases like "quicknode core workflow a", "quicknode-core-workflow-a", "blockchain RPC".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, quicknode, blockchain, web3, rpc, ethereum]
compatible-with: claude-code, codex, openclaw
---

# QuickNode Core Workflow A

## Overview
Build EVM transaction workflows: send ETH, interact with contracts, listen for events, and handle gas estimation.

## Prerequisites
- Completed `quicknode-hello-world`
- A funded wallet (use testnet for development)

## Instructions

### Step 1: Send ETH Transaction
```typescript
import { ethers } from 'ethers';

const provider = new ethers.JsonRpcProvider(process.env.QUICKNODE_ENDPOINT);
const wallet = new ethers.Wallet(process.env.PRIVATE_KEY!, provider);

const tx = await wallet.sendTransaction({
  to: '0xRecipientAddress',
  value: ethers.parseEther('0.01'),
});
console.log(`TX sent: ${tx.hash}`);
const receipt = await tx.wait();
console.log(`Confirmed in block ${receipt!.blockNumber}, gas used: ${receipt!.gasUsed}`);
```

### Step 2: Call Contract Write Function
```typescript
const contractAddress = '0xYourContract';
const abi = ['function transfer(address to, uint256 amount) returns (bool)'];
const contract = new ethers.Contract(contractAddress, abi, wallet);

const tx = await contract.transfer('0xRecipient', ethers.parseUnits('100', 18));
const receipt = await tx.wait();
console.log(`Transfer confirmed: ${receipt!.hash}`);
```

### Step 3: Listen for Events (WebSocket)
```typescript
const wsProvider = new ethers.WebSocketProvider(process.env.QUICKNODE_WSS);
const contract = new ethers.Contract(contractAddress, ['event Transfer(address indexed from, address indexed to, uint256 value)'], wsProvider);

contract.on('Transfer', (from, to, value, event) => {
  console.log(`Transfer: ${from} -> ${to}: ${ethers.formatUnits(value, 18)}`);
});
```

### Step 4: Gas Estimation
```typescript
const gasEstimate = await contract.transfer.estimateGas('0xRecipient', ethers.parseUnits('100', 18));
const feeData = await provider.getFeeData();
const totalCost = gasEstimate * (feeData.gasPrice || 0n);
console.log(`Estimated gas: ${gasEstimate}, cost: ${ethers.formatEther(totalCost)} ETH`);
```

## Output
- ETH transfer with receipt confirmation
- Smart contract interaction
- Real-time event listening via WebSocket
- Gas estimation before transactions

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `insufficient funds` | Wallet balance too low | Fund wallet or reduce amount |
| `nonce too low` | Nonce conflict | Get latest nonce: `provider.getTransactionCount(address)` |
| `gas required exceeds allowance` | Contract revert | Check contract requirements |

## Resources
- [QuickNode Ethereum API](https://www.quicknode.com/docs/ethereum)
- [ethers.js Documentation](https://docs.ethers.org/)

## Next Steps
NFT and token APIs: `quicknode-core-workflow-b`
