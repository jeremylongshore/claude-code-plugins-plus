# Examples

## Quick Start

### Check Current Gas Prices

```bash
python gas_optimizer.py current
```

Output:

```
CURRENT GAS PRICES (ETHEREUM)
============================================================
Base Fee:     25.50 gwei
Priority Fee: 1.50 gwei
Source:       rpc_feeHistory

PRICE TIERS
------------------------------------------------------------
Tier         Gas Price       Confirmation
------------------------------------------------------------
Slow         22.0 gwei       10+ blocks (~2+ min)
Standard     27.0 gwei       3-5 blocks (~1 min)
Fast         35.0 gwei       1-2 blocks (~30 sec)
Instant      45.0 gwei       Next block (~12 sec)
============================================================
```

### Estimate Transaction Cost

```bash
python gas_optimizer.py estimate --operation uniswap_v2_swap --all-tiers
```

Output:

```
COST ESTIMATE: UNISWAP_V2_SWAP
Gas Limit: 150,000
======================================================================
Tier         Gas Price       Cost ETH           Cost USD     Time
----------------------------------------------------------------------
Slow         22.0 gwei       0.003300           $9.90        10+ blocks
Standard     27.0 gwei       0.004050           $12.15       3-5 blocks
Fast         35.0 gwei       0.005250           $15.75       1-2 blocks
Instant      45.0 gwei       0.006750           $20.25       Next block
----------------------------------------------------------------------
Potential savings (Instant → Slow): $10.35 (51%)
```

### Find Optimal Transaction Window

```bash
python gas_optimizer.py optimal
```

Output:

```
OPTIMAL TRANSACTION WINDOW
============================================================
Recommendation: Best times: 4:00, 5:00, 3:00 UTC on Sunday

Expected Gas:   18.0 gwei
Potential Savings: 55.0% vs average

Timing:
  Best Hours: 04:00 - 06:00 UTC
============================================================

Current gas (27.0 gwei) is 33% higher than optimal.
Consider waiting for the recommended window.
```

## Cost Estimation Scenarios

### ETH Transfer

```bash
python gas_optimizer.py estimate --operation eth_transfer
```

### ERC-20 Token Approval + Swap

```bash
# First, approve the token
python gas_optimizer.py estimate --operation erc20_approve

# Then swap
python gas_optimizer.py estimate --operation uniswap_v3_swap --all-tiers
```

### NFT Mint

```bash
python gas_optimizer.py estimate --operation nft_mint --tier fast
```

### Custom Gas Limit

```bash
python gas_optimizer.py estimate --gas-limit 500000 --all-tiers
```

## Pattern Analysis

### View Hourly Patterns

```bash
python gas_optimizer.py patterns
```

Output:

```
HOURLY GAS PATTERNS (UTC)
============================================================
Hour     Avg Gas      Range                Status
------------------------------------------------------------
00:00    28.0         19 - 42
01:00    25.0         17 - 38              LOW
02:00    22.0         15 - 33              LOW
03:00    20.0         14 - 30              LOW
04:00    19.0         13 - 29              LOW
05:00    18.0         13 - 27              LOW
...
============================================================
LOW = Below average gas price
```

### View Daily Patterns

```bash
python gas_optimizer.py patterns --daily
```

### Predict Gas for Specific Time

```bash
# Predict for 2 PM today/tomorrow
python gas_optimizer.py predict --time 14

# Predict for specific datetime
python gas_optimizer.py predict --time "2025-01-20 14:00"
```

## Multi-Chain Comparison

### Compare All Chains

```bash
python gas_optimizer.py compare
```

Output:

```
MULTI-CHAIN GAS COMPARISON
======================================================================
Chain           Standard        Fast            Source
----------------------------------------------------------------------
ethereum        27.00           35.00           rpc_feeHistory
polygon         35.00           50.00           rpc_feeHistory
arbitrum        0.10            0.15            rpc_gasPrice
optimism        0.001           0.002           rpc_gasPrice
base            0.005           0.008           rpc_gasPrice
======================================================================
```

### Check Specific Chains

```bash
python gas_optimizer.py compare --chains "ethereum,polygon,arbitrum"
```

### Check Polygon Gas

```bash
python gas_optimizer.py current --chain polygon
```

## Base Fee History

### View Recent History

```bash
python gas_optimizer.py history --blocks 50
```

Output:

```
BASE FEE HISTORY (Last 50 blocks)
============================================================
Block        Base Fee (gwei)    Gas Used %
------------------------------------------------------------
19500100     25.50              75.5
19500101     26.10              82.3
19500102     27.80              95.1
...
------------------------------------------------------------
Average: 26.47 gwei | Min: 22.10 | Max: 35.80
```

## JSON Output

### Machine-Readable Output

```bash
python gas_optimizer.py current --json
```

Output:

```json
{
  "chain": "ethereum",
  "base_fee": 25500000000,
  "priority_fee": 1500000000,
  "gas_price": 27000000000,
  "slow": 22000000000,
  "standard": 27000000000,
  "fast": 35000000000,
  "instant": 45000000000,
  "timestamp": 1705784400,
  "source": "rpc_feeHistory"
}
```

### Pipe to jq

```bash
python gas_optimizer.py current --json | jq '.standard / 1e9'
# 27.0
```

## List Known Operations

```bash
python gas_optimizer.py operations
```

Output:

```
KNOWN OPERATIONS
==================================================
Operation                       Gas Limit
--------------------------------------------------
eth_transfer                       21,000
erc20_approve                      46,000
erc20_transfer                     65,000
nft_transfer                       85,000
bridge_deposit                    100,000
nft_mint                          150,000
uniswap_v2_swap                   150,000
sushiswap_swap                    150,000
aave_withdraw                     180,000
uniswap_v3_swap                   185,000
opensea_listing                   200,000
compound_supply                   200,000
aave_deposit                      250,000
curve_swap                        300,000
compound_borrow                   350,000
==================================================
```

## Practical Workflows

### Before a Large Transaction

```bash
# 1. Check current gas
python gas_optimizer.py current

# 2. Check if now is optimal
python gas_optimizer.py optimal

# 3. If not optimal, predict better time
python gas_optimizer.py predict --time 5

# 4. Estimate cost for your operation
python gas_optimizer.py estimate --operation uniswap_v3_swap --all-tiers
```

### Daily Monitoring

```bash
# Check patterns building up
python gas_optimizer.py patterns

# Compare with yesterday
python gas_optimizer.py history --blocks 7200  # ~1 day of blocks
```

### L2 Decision Making

```bash
# Compare L1 vs L2 costs
python gas_optimizer.py compare --chains "ethereum,arbitrum,optimism,base"

# Estimate same operation on L2
python gas_optimizer.py estimate --chain arbitrum --operation uniswap_v2_swap
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
