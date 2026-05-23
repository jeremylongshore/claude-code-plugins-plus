# Error Handling Reference

## API Errors

**Collection Not Found**

- Error: `404 Not Found` or empty response
- Cause: Invalid collection slug or collection delisted
- Solution: Verify slug on OpenSea; try contract address instead

**OpenSea Rate Limited**

- Error: `429 Too Many Requests`
- Cause: Exceeded API rate limits (4 req/sec without key)
- Solution: Add `OPENSEA_API_KEY`; wait and retry; use cached data

**OpenSea API Key Invalid**

- Error: `401 Unauthorized`
- Cause: Missing or invalid API key
- Solution: Set `OPENSEA_API_KEY` environment variable; regenerate key

**Alchemy API Error**

- Error: `403 Forbidden` or invalid response
- Cause: Missing or invalid Alchemy API key
- Solution: Set `ALCHEMY_API_KEY`; check key permissions

## IPFS Errors

**IPFS Gateway Timeout**

- Error: Request timeout fetching metadata
- Cause: IPFS gateway slow or content unavailable
- Solution: Automatic fallback to alternate gateways

**Invalid IPFS Hash**

- Error: Malformed IPFS URL or hash
- Cause: Corrupted metadata in contract
- Solution: Try fetching from OpenSea API instead

**Metadata Not JSON**

- Error: Failed to parse metadata
- Cause: Non-standard or corrupted metadata format
- Solution: Token skipped from analysis

## Data Errors

**No Tokens Found**

- Error: Empty token list
- Cause: Collection too new, unlaunched, or hidden
- Solution: Wait for collection to be indexed; verify slug

**Missing Attributes**

- Error: Token has no traits
- Cause: Revealed/unrevealed state or non-standard format
- Solution: Treated as all "None" traits

**Token ID Not Found**

- Error: Requested token not in fetched data
- Cause: Token ID outside fetched range or doesn't exist
- Solution: Increase `--limit` to fetch more tokens

## Cache Errors

**Cache Read Failed**

- Error: JSONDecodeError on cache load
- Cause: Corrupted cache file
- Solution: Clear cache with `cache --clear`

**Cache Directory Permission**

- Error: Cannot write to ~/.nft_cache
- Cause: Permission issues
- Solution: Check directory permissions; use different cache path

## Algorithm Errors

**Division by Zero**

- Error: Cannot calculate rarity
- Cause: Trait frequency is 0 (shouldn't happen)
- Solution: Uses minimum frequency of 1/total_supply

**No Traits to Analyze**

- Error: Empty trait map
- Cause: No valid attributes in metadata
- Solution: Check metadata format; verify collection support

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `OPENSEA_API_KEY` | OpenSea API authentication | None (rate limited) |
| `ALCHEMY_API_KEY` | Alchemy NFT API | None (limited features) |

## Fallback Chain

```
1. OpenSea API → Primary source
   ↓ fails
2. Alchemy API → Backup metadata
   ↓ fails
3. Direct IPFS → Raw metadata fetch
   ↓ fails
4. Cache → Last known data
   ↓ fails
5. Error → User notification
```

## Common Fixes

1. **Slow analysis**: Reduce `--limit`; use cached data
2. **Incomplete data**: Increase `--limit`
3. **Wrong rankings**: Verify algorithm choice; check for unrevealed tokens
4. **API errors**: Set API keys; check rate limits

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
