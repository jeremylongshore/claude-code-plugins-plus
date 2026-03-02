# Error Handling Guide

## RPC Connection Errors

### Connection Refused
```
Error: Connection refused to RPC endpoint
```
**Cause**: RPC endpoint is down or unreachable
**Solution**:
- Check if RPC URL is correct
- Try alternative endpoint (Alchemy, Chainstack, Infura, or public RPC)
- Verify network connectivity

### Timeout
```
Error: Request timed out
```
**Cause**: RPC node is slow or overloaded
**Solution**:
- Increase timeout setting
- Switch to faster RPC provider
- Reduce request frequency

### Rate Limited
```
Error: Too many requests (429)
```
**Cause**: Exceeded RPC provider rate limits
**Solution**:
- Reduce polling frequency
- Upgrade RPC tier (paid Alchemy, Chainstack, or Infura plans)
- Use multiple RPC endpoints

## Mempool Access Errors

### txpool_content Not Available
```
Error: txpool_content not supported
```
**Cause**: Not all nodes support txpool methods
**Solution**:
- Use Geth node with txpool enabled
- Try eth_pendingTransactions instead
- Use mock data for demo purposes

### Empty Mempool
```
No pending transactions found
```
**Cause**: Mempool is empty or access limited
**Solution**:
- Normal during low activity periods
- Verify RPC supports mempool access
- Check if node is fully synced

## Transaction Decoding Errors

### Unknown Method Signature
```
Warning: Unknown method 0x12345678
```
**Cause**: Method signature not in known ABI list
**Solution**:
- Transaction will show as "Unknown" type
- Add ABI to decoder if needed
- Use Etherscan to look up contract ABI

### Invalid Input Data
```
Error: Cannot decode input data
```
**Cause**: Malformed or non-standard input
**Solution**:
- Skip transaction, continue analysis
- Raw data still available

## Gas Analysis Errors

### No Sample Data
```
Warning: Insufficient data for gas analysis
```
**Cause**: Too few pending transactions
**Solution**:
- Use default recommendations
- Wait for more mempool activity
- Reduce sample requirements

## MEV Detection Errors

### Pool Data Unavailable
```
Warning: Cannot fetch pool reserves
```
**Cause**: DEX subgraph or pool query failed
**Solution**:
- MEV detection will have lower confidence
- Use estimated values
- Check subgraph health

## Debugging

### Enable Verbose Mode
```bash
python mempool_analyzer.py -v pending
```

### Check Connection
```bash
python mempool_analyzer.py status
```

### Test RPC Endpoint
```bash
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  YOUR_RPC_URL
```
