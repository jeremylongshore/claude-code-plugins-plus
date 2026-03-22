---
name: quicknode-common-errors
description: |
  Diagnose and fix QuickNode RPC errors: nonce issues, gas failures, rate limits.
  Use when encountering blockchain RPC errors, failed transactions, or connection issues.
  Trigger with phrases like "quicknode error", "RPC error", "nonce too low", "gas estimation failed".
allowed-tools: Read, Grep, Bash(curl:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, quicknode, blockchain, web3, debugging]
compatible-with: claude-code, codex, openclaw
---

# QuickNode Common Errors

## Overview
Quick reference for the top blockchain RPC errors when using QuickNode endpoints with ethers.js or viem.

## Prerequisites
- QuickNode endpoint configured
- ethers.js or viem installed

## Instructions

### Error 1: Nonce Too Low
```
Error: nonce has already been used (error={"code":-32000,"message":"nonce too low"})
```
**Fix:**
```typescript
// Get the correct nonce before sending
const nonce = await provider.getTransactionCount(wallet.address, 'pending');
const tx = await wallet.sendTransaction({ ...txData, nonce });
```

### Error 2: Insufficient Funds
```
Error: insufficient funds for intrinsic transaction cost
```
**Fix:**
```typescript
const balance = await provider.getBalance(wallet.address);
const gasEstimate = await provider.estimateGas(txData);
const feeData = await provider.getFeeData();
const totalCost = gasEstimate * feeData.gasPrice! + txData.value;
if (balance < totalCost) {
  console.error(`Need ${ethers.formatEther(totalCost)} ETH, have ${ethers.formatEther(balance)}`);
}
```

### Error 3: Gas Estimation Failed (Call Revert)
```
Error: execution reverted (reason="ERC20: transfer amount exceeds balance")
```
**Fix:** The contract function would revert. Check contract requirements:
```typescript
try {
  const gas = await contract.transfer.estimateGas(to, amount);
} catch (err) {
  console.error('Revert reason:', err.reason);
  // Check: sufficient token balance, approvals, contract state
}
```

### Error 4: Rate Limited (429)
```
Error: 429 Too Many Requests
```
**Fix:** Implement exponential backoff or upgrade plan:
```typescript
async function retryRpc<T>(fn: () => Promise<T>, retries = 3): Promise<T> {
  for (let i = 0; i < retries; i++) {
    try { return await fn(); }
    catch (err: any) {
      if (err.code === 'SERVER_ERROR' && i < retries - 1) {
        await new Promise(r => setTimeout(r, 1000 * Math.pow(2, i)));
        continue;
      }
      throw err;
    }
  }
  throw new Error('Max retries');
}
```

### Error 5: Method Not Found
```
Error: Method not found — qn_getTokenMetadataByContractAddress
```
**Fix:** This method requires an add-on. Enable it in QuickNode Dashboard > Endpoints > Add-ons.

### Error 6: WebSocket Connection Dropped
```
Error: WebSocket connection closed unexpectedly
```
**Fix:**
```typescript
const wsProvider = new ethers.WebSocketProvider(process.env.QUICKNODE_WSS);
wsProvider.websocket.on('close', () => {
  console.log('WebSocket closed, reconnecting...');
  // Reconnect logic
});
```

## Output
- Error identified from RPC response
- Targeted fix applied
- Transaction successfully sent or contract call succeeded

## Error Handling
| RPC Code | Meaning | Retryable |
|----------|---------|-----------|
| -32000 | Nonce/gas issue | Fix and retry |
| -32602 | Invalid params | No — fix request |
| -32603 | Internal error | Yes — retry |
| 429 | Rate limited | Yes — backoff |

## Resources
- [QuickNode Ethereum API](https://www.quicknode.com/docs/ethereum)
- [ethers.js Error Handling](https://docs.ethers.org/)

## Next Steps
For debugging, see `quicknode-debug-bundle`.
