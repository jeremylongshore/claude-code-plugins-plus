---
name: alchemy-common-errors
description: |
  Diagnose and fix common Alchemy SDK and Web3 API errors.
  Use when encountering rate limits, RPC failures, invalid parameters,
  or blockchain query errors with the Alchemy SDK.
  Trigger: "alchemy error", "alchemy not working", "alchemy 429",
  "alchemy debug", "fix alchemy issue".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, blockchain, web3, alchemy, troubleshooting]
compatible-with: claude-code
---

# Alchemy Common Errors

## Overview

Troubleshooting guide for Alchemy SDK errors covering rate limits, RPC failures, invalid parameters, and network-specific issues.

## Error Reference

### Authentication & Rate Limits

| HTTP Code | Error | Root Cause | Fix |
|-----------|-------|-----------|-----|
| `401` | Unauthorized | Invalid or missing API key | Verify key in Alchemy Dashboard |
| `403` | Forbidden | API key disabled or app deleted | Create new app in Dashboard |
| `429` | Too Many Requests | Rate limit exceeded | Implement backoff; upgrade plan |
| `429` | Compute Units exceeded | CU quota depleted | Check CU usage in Dashboard |

### Alchemy Rate Limits by Plan

| Plan | Compute Units/sec | Throughput |
|------|-------------------|------------|
| Free | 330 CU/s | ~25 requests/s |
| Growth | 660 CU/s | ~50 requests/s |
| Scale | Custom | Custom |

### RPC & Query Errors

```typescript
// Common RPC error handler
import { Alchemy, Network } from 'alchemy-sdk';

async function safeAlchemyCall<T>(
  operation: () => Promise<T>,
  context: string
): Promise<T | null> {
  try {
    return await operation();
  } catch (error: any) {
    const code = error.code || error.response?.status;

    switch (code) {
      case -32602: // Invalid params
        console.error(`[${context}] Invalid parameters: ${error.message}`);
        console.error('Common causes: wrong address format, invalid block number, missing 0x prefix');
        break;

      case -32600: // Invalid request
        console.error(`[${context}] Malformed JSON-RPC request`);
        break;

      case -32601: // Method not found
        console.error(`[${context}] RPC method not available on this network`);
        console.error('Some Enhanced APIs are Ethereum-only');
        break;

      case -32000: // Server error
        console.error(`[${context}] Node server error — usually transient, retry`);
        break;

      case 429:
        const retryAfter = error.response?.headers?.['retry-after'] || 1;
        console.error(`[${context}] Rate limited — retry after ${retryAfter}s`);
        break;

      default:
        console.error(`[${context}] Unknown error: ${code} — ${error.message}`);
    }
    return null;
  }
}
```

### NFT API Errors

| Error | Root Cause | Fix |
|-------|-----------|-----|
| Empty `ownedNfts` | Address has no NFTs on this chain | Check correct network |
| Missing `image.cachedUrl` | IPFS/Arweave gateway timeout | Use `image.originalUrl` fallback |
| `getNftsForContract` empty | Contract not indexed | Wait for indexing; try `refreshContract` |
| Spam NFTs in results | No spam filter | Add `excludeFilters: ['SPAM']` option |
| `getNftMetadataBatch` fails | Batch too large | Limit to 100 tokens per batch |

### Enhanced API Errors

| Error | Root Cause | Fix |
|-------|-----------|-----|
| `getAssetTransfers` empty | Wrong category | Include all: EXTERNAL, ERC20, ERC721, ERC1155 |
| `getTokenBalances` timeout | Too many tokens | Paginate or use specific contract addresses |
| `getTokenMetadata` null fields | Token not verified | Handle null `name`/`symbol` gracefully |
| WebSocket disconnect | Idle timeout (5 min) | Implement auto-reconnect logic |

### Network-Specific Issues

```typescript
// Diagnostic function
async function diagnoseAlchemyIssue(alchemy: Alchemy): Promise<string[]> {
  const issues: string[] = [];

  try {
    const blockNumber = await alchemy.core.getBlockNumber();
    console.log(`Connected: block #${blockNumber}`);
  } catch (err: any) {
    if (err.message?.includes('apiKey')) issues.push('API key invalid or missing');
    else if (err.code === 'ECONNREFUSED') issues.push('Cannot reach Alchemy servers — check network');
    else issues.push(`Connection error: ${err.message}`);
  }

  return issues;
}
```

## Quick Diagnostic

```bash
# Test Alchemy API directly
curl -s "https://eth-mainnet.g.alchemy.com/v2/${ALCHEMY_API_KEY}" \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":0}' | jq .

# Check CU usage (requires auth token)
curl -s "https://dashboard.alchemy.com/api/stats" \
  -H "Authorization: Bearer ${ALCHEMY_AUTH_TOKEN}" | jq .
```

## Output

- Error classified by type (auth, rate limit, RPC, network)
- Root cause identified with specific fix
- Diagnostic function for automated troubleshooting

## Resources

- [Alchemy Error Codes](https://www.alchemy.com/docs/reference/error-reference)
- [Alchemy Rate Limits](https://www.alchemy.com/docs/reference/rate-limits)
- [JSON-RPC Error Codes](https://www.jsonrpc.org/specification#error_object)

## Next Steps

For collecting debug bundles, see `alchemy-debug-bundle`.
