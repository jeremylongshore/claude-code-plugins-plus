# Usage Examples

## Recent Token Launches

### Basic Usage

```bash
# Show launches from last 24 hours on Ethereum
python launch_tracker.py recent --chain ethereum

# Output:
# NEW TOKEN LAUNCHES
# ==========================================================================================
# Time         Token                DEX             Chain      Risk            Pair
# ------------------------------------------------------------------------------------------
# 2m ago       PEPE2.0              Uniswap V2      ethereum   [HIGH RISK: 75] 0x1234...5678
# 15m ago      DOGE420              Uniswap V2      ethereum   [MEDIUM: 45]    0xabcd...efgh
# 1h ago       SAFE                 SushiSwap       ethereum   [OK: 15]        0x9876...5432
# ==========================================================================================
# Total: 47 new pairs
```

### With Risk Analysis

```bash
# Include token and contract analysis
python launch_tracker.py recent --chain base --analyze --hours 12

# Output includes enriched token data with risk scores
```

### Filter by DEX

```bash
# Only show Uniswap V2 launches
python launch_tracker.py recent --chain ethereum --dex "Uniswap V2"
```

### JSON Output

```bash
# Get JSON for programmatic use
python launch_tracker.py -f json recent --chain bsc --hours 6 --limit 10
```

## Token Details

### Get Full Token Information

```bash
python launch_tracker.py detail \
  --address 0x6982508145454ce325ddbe47a25d4ec3d2311933 \
  --chain ethereum

# Output:
# TOKEN LAUNCH: PEPE
# ============================================================
# Name:         Pepe
# Symbol:       PEPE
# Address:      0x6982508145454ce325ddbe47a25d4ec3d2311933
# Pair:         Unknown
#
# LAUNCH INFO
# ------------------------------------------------------------
# DEX:          Unknown
# Chain:        ETHEREUM
# Block:        0
# Time:         2024-01-20 15:30 (5m ago)
# Tx:
#
# TOKEN INFO
# ------------------------------------------------------------
# Decimals:     18
# Total Supply: 420.69T
# Owner:        None
# Verified:     Yes
#
# RISK ANALYSIS
# ------------------------------------------------------------
# Risk Score:   25/100 [LOW: 25]
# Is Proxy:     No
# Ownership:    Renounced
#
# Indicators:
#   .  Has burn: Contract has burn function
#      Ownership Renounced: Ownership has been renounced
#
# LINKS
# ------------------------------------------------------------
# Explorer:     https://etherscan.io/address/0x698250...
# DEXScreener:  https://dexscreener.com/ethereum/Unknown
# ============================================================
```

## Risk Analysis

### Analyze Token Contract

```bash
python launch_tracker.py risk \
  --address 0x1234567890abcdef1234567890abcdef12345678 \
  --chain ethereum

# Output:
# RISK ANALYSIS
# ============================================================
# Address:      0x1234567890abcdef1234567890abcdef12345678
# Chain:        ETHEREUM
#
# Risk Score:   75/100 [HIGH RISK: 75]
# Risk Level:   HIGH RISK
#
# CONTRACT INFO
# ------------------------------------------------------------
# Bytecode:     8,456 bytes
# Is Proxy:     Yes
# Ownership:    Active
#
# RISK INDICATORS
# ------------------------------------------------------------
#   !! [HIGH  ] Has mint
#               Contract has mint function
#   !  [MEDIUM] Proxy Contract
#               Contract is a proxy - implementation can be changed
#   !  [MEDIUM] Not Verified
#               Contract source code not verified
#   .  [LOW   ] Has Owner
#               Contract has active owner: 0x9876543210ab...
#
# ============================================================
```

### With Etherscan Verification

```bash
# Include contract verification check
python launch_tracker.py risk \
  --address 0x... \
  --chain ethereum \
  --etherscan-key YOUR_API_KEY
```

## Launch Summary

### Cross-Chain Summary

```bash
python launch_tracker.py summary --hours 24

# Output:
# LAUNCHES BY CHAIN
# ========================================
#   BSC                      156
#   ETHEREUM                  89
#   BASE                      67
#   ARBITRUM                  45
#   POLYGON                   34
# ----------------------------------------
#   TOTAL                    391
# ========================================
#
# LAUNCHES BY DEX
# ========================================
#   bsc:PancakeSwap V2       134
#   ethereum:Uniswap V2       72
#   base:Aerodrome            52
#   arbitrum:Camelot          38
#   bsc:PancakeSwap V3        22
# ========================================
```

### Specific Chains Only

```bash
# Only Ethereum and Base
python launch_tracker.py summary --chains ethereum,base --hours 12
```

## List DEXes and Chains

### Show Supported Chains

```bash
python launch_tracker.py chains

# Output:
# SUPPORTED CHAINS
# ======================================================================
# Chain           Name                 ID         Symbol   Block
# ----------------------------------------------------------------------
# ethereum        Ethereum             1          ETH      12.0s
# bsc             BNB Chain            56         BNB      3.0s
# arbitrum        Arbitrum One         42161      ETH      0.25s
# base            Base                 8453       ETH      2.0s
# polygon         Polygon              137        MATIC    2.0s
# ======================================================================
```

### Show DEXes for Chain

```bash
python launch_tracker.py dexes --chain bsc

# Output:
# SUPPORTED DEXES ON BSC
# ============================================================
#   PancakeSwap V2            (v2)
#     Factory: 0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73
#   PancakeSwap V3            (v3)
#     Factory: 0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865
# ============================================================
```

### All DEXes (JSON)

```bash
python launch_tracker.py -f json dexes
```

## Custom RPC Usage

### Use Custom RPC Endpoint

```bash
python launch_tracker.py recent \
  --chain ethereum \
  --rpc-url https://mainnet.infura.io/v3/YOUR_PROJECT_ID
```

### Via Environment Variable

```bash
export ETHEREUM_RPC_URL=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
python launch_tracker.py recent --chain ethereum
```

## Verbose Output

### Debug Mode

```bash
python launch_tracker.py --verbose recent --chain base --hours 1

# Shows:
# RPC: eth_blockNumber
# RPC: eth_getLogs
# RPC: eth_getBlockByNumber
#   [1/12] MEME
#   [2/12] WAGMI
# ...
```

## Common Workflows

### Find High-Risk New Tokens

```bash
# Get recent launches with analysis, output as JSON
python launch_tracker.py -f json recent \
  --chain ethereum \
  --hours 6 \
  --analyze \
  --limit 100 > launches.json

# Filter for high risk (in Python/jq)
jq '.[] | select(.analysis.risk_score >= 70)' launches.json
```

### Monitor Multiple Chains

```bash
#!/bin/bash
for chain in ethereum bsc base arbitrum; do
  echo "=== $chain ==="
  python launch_tracker.py recent --chain $chain --hours 1 --limit 5
done
```

### Export to CSV (via jq)

```bash
python launch_tracker.py -f json recent --chain ethereum --hours 24 | \
  jq -r '.[] | [.pair.timestamp, .pair.dex, .token_info.symbol // "???", .analysis.risk_score // 0] | @csv'
```

## Integration Examples

### Python Import

```python
from event_monitor import EventMonitor
from token_analyzer import TokenAnalyzer

# Monitor new pairs
monitor = EventMonitor(chain="ethereum")
pairs = monitor.get_recent_pairs(hours=1)

for pair in pairs:
    new_token = monitor.identify_new_token(pair)
    print(f"New token: {new_token} on {pair.dex}")

# Analyze risk
analyzer = TokenAnalyzer(chain="ethereum")
for pair in pairs[:5]:
    new_token = monitor.identify_new_token(pair)
    analysis = analyzer.analyze_contract(new_token)
    print(f"  Risk: {analysis.risk_score}/100")
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
