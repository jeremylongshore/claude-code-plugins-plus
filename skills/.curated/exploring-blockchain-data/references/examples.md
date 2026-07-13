# Usage Examples

## Transaction Queries

### Basic Transaction Lookup

```bash
python blockchain_explorer.py tx 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
```

Output:

```
╔══════════════════════════════════════════════════════════════════════╗
║  Transaction Details                                                  ║
╠══════════════════════════════════════════════════════════════════════╣
║  Hash:     0x1234567890abcdef1234567890abcdef1234567890ab            ║
║  Chain:    Ethereum                                                   ║
║  Status:   ✓ success                                                  ║
║  Block:    18500000                                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  From:     0xabcdef1234567890abcdef1234567890abcdef12                ║
║  To:       0x1234567890abcdef1234567890abcdef12345678                ║
║  Value:    1.5000 ETH                                                 ║
╠══════════════════════════════════════════════════════════════════════╣
║  Gas Price: 25.50 Gwei                                                ║
║  Gas Limit: 21000                                                     ║
║  Gas Used:  21000                                                     ║
║  Gas Cost:  0.000535 ETH                                              ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Transaction with Decoded Data

```bash
python blockchain_explorer.py tx 0x... --detailed
```

Shows decoded function name and protocol identification.

### Cross-Chain Transaction

```bash
# Query on Polygon
python blockchain_explorer.py tx 0x... --chain polygon

# Query on Arbitrum
python blockchain_explorer.py tx 0x... --chain arbitrum

# Query on BSC
python blockchain_explorer.py tx 0x... --chain bsc
```

## Address Queries

### Check Wallet Balance

```bash
python blockchain_explorer.py address 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
```

Output:

```
╔══════════════════════════════════════════════════════════════════════╗
║  Address Details                                                      ║
╠══════════════════════════════════════════════════════════════════════╣
║  Address:  0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045                ║
║  Chain:    Ethereum                                                   ║
╠══════════════════════════════════════════════════════════════════════╣
║  Balance:  1,234.5678 ETH                                             ║
║  Txns:     15,432                                                     ║
╠══════════════════════════════════════════════════════════════════════╣
║  Explorer: https://etherscan.io/address/0xd8dA6BF26964aF9...         ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Address with Transaction History

```bash
python blockchain_explorer.py address 0x... --history --limit 10
```

### Address with Token Transfers

```bash
python blockchain_explorer.py address 0x... --tokens
```

### Full Address Analysis

```bash
python blockchain_explorer.py address 0x... --history --tokens --limit 50
```

## Block Queries

### Latest Block

```bash
python blockchain_explorer.py block latest
```

### Specific Block

```bash
python blockchain_explorer.py block 18500000
```

### Block on Different Chain

```bash
python blockchain_explorer.py block latest --chain polygon
```

## Token Queries

### Check Token Balance

```bash
# Check USDC balance
python blockchain_explorer.py token 0xYourWallet 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
```

Output:

```
Token Balance
============================================================
Address:  0xYourWallet
Token:    USD Coin (USDC)
Contract: 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48
Chain:    Ethereum
Balance:  1,000.000000 USDC
Value:    $1,000.00
```

### Common Token Contracts

| Token | Ethereum Contract |
|-------|-------------------|
| USDC | 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 |
| USDT | 0xdac17f958d2ee523a2206206994597c13d831ec7 |
| DAI | 0x6b175474e89094c44da98b954eedeac495271d0f |
| WETH | 0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2 |
| LINK | 0x514910771af9ca656af840dff83e8264ecf986ca |

## Output Formats

### JSON Output

```bash
python blockchain_explorer.py tx 0x... --format json
```

Output:

```json
{
  "hash": "0x1234...",
  "chain": "Ethereum",
  "status": "success",
  "block_number": 18500000,
  "from": "0xabcd...",
  "to": "0x1234...",
  "value": 1.5,
  "gas_price_gwei": 25.5,
  "gas_used": 21000
}
```

### CSV Output

```bash
python blockchain_explorer.py history 0x... --format csv > transactions.csv
```

### Redirect to File

```bash
python blockchain_explorer.py address 0x... --history --format json > wallet_analysis.json
```

## Programmatic Usage

### Python Script

```python
from chain_client import ChainClient
from token_resolver import TokenResolver

# Initialize clients
client = ChainClient(chain="ethereum")
resolver = TokenResolver(chain="ethereum")

# Query transaction
tx = client.get_transaction("0x1234...")
print(f"Status: {tx['status']}")
print(f"Value: {tx['value']} ETH")

# Query balance
balance = client.get_balance("0xabcd...")
print(f"Balance: {balance['balance']} ETH")

# Get token info
token = resolver.resolve("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
print(f"Token: {token.name} ({token.symbol})")
print(f"Price: ${token.price_usd}")
```

### Multi-Chain Query

```python
from chain_client import ChainClient, CHAINS

address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"

for chain in ["ethereum", "polygon", "arbitrum"]:
    client = ChainClient(chain=chain)
    balance = client.get_balance(address)
    print(f"{chain}: {balance['balance']:.4f} {balance['symbol']}")
```

## Whale Watching Examples

### Track Large Holder

```bash
# Vitalik's address transaction history
python blockchain_explorer.py history 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --limit 100

# Token transfers for whale
python blockchain_explorer.py transfers 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --limit 50
```

### DEX Transaction Analysis

```bash
# Query Uniswap swap transaction
python blockchain_explorer.py tx 0x... --detailed
```

Shows decoded swap parameters: `swapExactTokensForTokens`, amounts, path.

## Debugging Tips

### Verbose Mode

```bash
python blockchain_explorer.py tx 0x... --verbose
```

Shows API calls, timing, and cache status.

### Test RPC Connection

```bash
python blockchain_explorer.py block latest --verbose --chain ethereum
```

Verifies RPC endpoint is working.

### Check API Key

```bash
export ETHERSCAN_API_KEY=your_key
python blockchain_explorer.py address 0x... --verbose
```

Confirms API key is being used.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
