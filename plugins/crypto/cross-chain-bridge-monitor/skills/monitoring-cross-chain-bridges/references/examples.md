# Usage Examples

## Bridge TVL Rankings

### Show Top Bridges by TVL

```bash
python bridge_monitor.py tvl

# Output:
# BRIDGE TVL RANKINGS
# ================================================================================
# Rank   Bridge                    Total TVL             Chains
# --------------------------------------------------------------------------------
# 1      Stargate                  $1.24B                8
# 2      Across                    $456.78M              6
# 3      Synapse                   $234.56M              15
# 4      Hop                       $123.45M              6
# ================================================================================
```

### TVL as JSON

```bash
python bridge_monitor.py -f json tvl --limit 5
```

## List All Bridges

### Show Bridge Rankings by Volume

```bash
python bridge_monitor.py bridges

# Output:
# CROSS-CHAIN BRIDGES
# ==========================================================================================
# Rank   Bridge                    24h Volume      Chains     Change
# ------------------------------------------------------------------------------------------
# 1      Stargate                  $245.67M        8          +12.34%
# 2      Across Protocol           $123.45M        6          -5.67%
# 3      Synapse                   $98.76M         15         +8.90%
# ==========================================================================================
# Total bridges: 45
```

### Filter by Chain

```bash
# Show bridges supporting Arbitrum
python bridge_monitor.py bridges --chain arbitrum
```

## Bridge Details

### Get Detailed Bridge Info

```bash
python bridge_monitor.py detail --bridge stargate

# Output:
# BRIDGE: Stargate
# ============================================================
# Name:         stargate
# ID:           1
#
# VOLUME
# ------------------------------------------------------------
# 24h Volume:   $245.67M
# Previous 24h: $218.92M
# Change:       +12.21%
#
# SUPPORTED CHAINS
# ------------------------------------------------------------
#   ethereum, arbitrum, optimism, polygon, bsc
#   avalanche, fantom, base
#
# TVL BY CHAIN
# ------------------------------------------------------------
#   ethereum             $456.78M
#   arbitrum             $234.56M
#   optimism             $123.45M
#   ...
#   Total                $1.24B
# ============================================================
```

## Compare Bridge Routes

### Compare Fees for a Route

```bash
python bridge_monitor.py compare --source ethereum --dest arbitrum --amount 1000 --token USDC

# Output:
# BRIDGE FEE COMPARISON: ETHEREUM → ARBITRUM
# Amount: 1000 USDC
# ================================================================================
# Bridge               Bridge Fee      Gas (Total)     Total Fee       Time
# --------------------------------------------------------------------------------
# Across               $0.4000         $0.0060         $0.4060         ~1 min
# Stargate             $0.6000         $0.0150         $0.6150         ~2 min
# LayerZero            $0.6000         $0.0110         $0.6110         ~3 min
# Wormhole             $1.0000         $0.0070         $1.0070         ~15 min
# ================================================================================
# Cheapest: Across
# Fastest: Across
```

### Compare Large Transfer

```bash
python bridge_monitor.py compare \
  --source ethereum \
  --dest base \
  --amount 100000 \
  --token USDC
```

### Compare as JSON

```bash
python bridge_monitor.py -f json compare \
  --source ethereum \
  --dest arbitrum \
  --amount 5000 \
  --token USDC
```

## Track Transactions

### Track a Bridge Transaction

```bash
python bridge_monitor.py tx --tx-hash 0x1234...abcd

# Output:
# BRIDGE TRANSACTION STATUS
# ============================================================
# TX Hash:      0x1234...abcd
# Bridge:       Stargate
# Route:        ethereum → arbitrum
# Status:       [OK] COMPLETED
#
# CONFIRMATION
# ------------------------------------------------------------
# Source Chain: Confirmed
# Dest Chain:   Confirmed
# Amount:       1000.00 USDC
# Dest TX:      0xabcd...1234
# Timestamp:    2024-01-20 15:30:45
# ============================================================
```

### Track with Bridge Hint

```bash
# Faster tracking if you know the bridge
python bridge_monitor.py tx \
  --tx-hash 0x1234...abcd \
  --bridge wormhole
```

### Track with Source Chain

```bash
python bridge_monitor.py tx \
  --tx-hash 0x1234...abcd \
  --chain ethereum
```

## List Supported Chains

### Show All Chains

```bash
python bridge_monitor.py chains

# Output:
# SUPPORTED CHAINS
# ============================================================
#   ethereum        bsc             polygon         arbitrum
#   optimism        base            avalanche       fantom
#   linea           scroll          zksync          mantle
# ============================================================
# Total: 45 chains
```

## List Bridge Protocols

### Show Supported Protocols

```bash
python bridge_monitor.py protocols

# Output:
# SUPPORTED BRIDGE PROTOCOLS
# ============================================================
#
# Wormhole
# ----------------------------------------
#   Chains: ethereum, solana, bsc, polygon, avalanche
#           +15 more
#
# LayerZero
# ----------------------------------------
#   Chains: ethereum, bsc, avalanche, polygon, arbitrum
#           +45 more
#
# Stargate
# ----------------------------------------
#   Chains: ethereum, bsc, avalanche, polygon, arbitrum
#           +3 more
#
# Across
# ----------------------------------------
#   Chains: ethereum, optimism, arbitrum, polygon, base
#           +1 more
#
# ============================================================
# Total protocols: 4
```

## JSON Output

### Any Command with JSON

```bash
# TVL as JSON
python bridge_monitor.py -f json tvl

# Bridges as JSON
python bridge_monitor.py -f json bridges --limit 10

# Detail as JSON
python bridge_monitor.py -f json detail --bridge across

# Transaction as JSON
python bridge_monitor.py -f json tx --tx-hash 0x...
```

## Common Workflows

### Find Best Route for Large Transfer

```bash
# Compare routes
python bridge_monitor.py compare -s ethereum -d arbitrum -a 50000 -t USDC

# Check bridge liquidity
python bridge_monitor.py detail --bridge stargate

# Verify TVL is sufficient
python bridge_monitor.py tvl
```

### Monitor Bridge After Transfer

```bash
# Get tx hash from wallet/explorer, then track
python bridge_monitor.py tx --tx-hash 0x...

# If pending, check again later
watch -n 30 "python bridge_monitor.py tx --tx-hash 0x..."
```

### Research Bridge Safety

```bash
# Check bridge volume and TVL trends
python bridge_monitor.py detail --bridge synapse

# Compare with other bridges
python bridge_monitor.py bridges | head -20
```

## Integration Examples

### Python Import

```python
from bridge_fetcher import BridgeFetcher
from protocol_adapters import get_all_adapters
from tx_tracker import TxTracker

# Get bridge data
fetcher = BridgeFetcher()
bridges = fetcher.get_all_bridges()
print(f"Found {len(bridges)} bridges")

# Check TVL
for bridge in bridges[:5]:
    tvl = fetcher.get_bridge_tvl(bridge.id)
    print(f"{bridge.display_name}: ${tvl.total_tvl:,.0f}")

# Track transaction
tracker = TxTracker()
status = tracker.track_bridge_tx("0x...")
print(f"Status: {status.status}")
```

### Shell Script Monitoring

```bash
#!/bin/bash
# Monitor bridge TVL changes

while true; do
    echo "=== $(date) ==="
    python bridge_monitor.py tvl --limit 5
    sleep 300  # Check every 5 minutes
done
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
