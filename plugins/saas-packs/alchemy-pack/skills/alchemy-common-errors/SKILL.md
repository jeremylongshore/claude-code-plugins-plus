---
name: alchemy-common-errors
description: 'Diagnose and fix common Alchemy SDK and Web3 API errors.

  Use when encountering rate limits, RPC failures, invalid parameters,

  or blockchain query errors with the Alchemy SDK.

  Trigger: "alchemy error", "alchemy not working", "alchemy 429",

  "alchemy debug", "fix alchemy issue".

  '
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- blockchain
- web3
- alchemy
- troubleshooting
compatibility: Designed for Claude Code
---
# Alchemy Common Errors

## Overview

Troubleshooting guide for Alchemy SDK errors covering rate limits, RPC failures, invalid parameters, and network-specific issues.

## Prerequisites

- A reproducible failing request that records its network, method, sanitized
  parameters, timestamp, response code, and request/correlation ID where
  available—never the API key or private key.
- Access to the appropriate Alchemy dashboard and a non-production key when
  testing a fix.
- A defined retry budget and an application fallback for requests that cannot
  safely be retried.

## Instructions

1. Classify the failure with the error reference and confirm the intended
   network, RPC method, and parameter shape.
2. Reproduce it with a scoped development key or a public test fixture, then
   inspect account limits and service status without exposing credentials.
3. Apply the smallest appropriate repair: correct parameters, back off for
   `429`, paginate a large query, or switch to the documented supported API.
4. Verify the corrected request and record the sanitized outcome; escalate
   persistent provider failures with the correlation or request ID.

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

## Examples

When a testnet `getAssetTransfers` call returns `429`, retain the sanitized
method, network, response headers, and request ID, then make the retry helper
honor `Retry-After` within the configured budget. Confirm the retry succeeds
against the expected testnet or produces a controlled unavailable result when
the budget is exhausted. If the dashboard shows a disabled key or depleted
quota, stop retries and correct the account configuration; do not substitute a
production credential or place it in a curl command committed to the project.

## Error Handling

| Failure class | Safe handling |
|---------------|---------------|
| `401` or `403` | Stop the request, verify the scoped key’s application and network, and rotate a suspected exposure. |
| `429` or transient `5xx` | Use bounded backoff and surface an operator-visible unavailable state after the retry budget. |
| Invalid RPC parameters | Validate address, chain, and block inputs before retrying; a retry cannot repair malformed input. |
| Unknown provider failure | Preserve only sanitized request metadata and escalate with the request/correlation ID. |

## Resources

- [Alchemy Error Codes](https://www.alchemy.com/docs/reference/error-reference)
- Alchemy Rate Limits
- [JSON-RPC Error Codes](https://www.jsonrpc.org/specification#error_object)

## Next Steps

For collecting debug bundles, see `alchemy-debug-bundle`.
