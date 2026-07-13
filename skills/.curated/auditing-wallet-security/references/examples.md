# Usage Examples

## Basic Commands

### List All Token Approvals

```bash
# Show all active approvals on Ethereum
python wallet_auditor.py approvals 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Output:
# ═══════════════════════════════════════════════════════════════════
#                       APPROVAL SUMMARY
# ═══════════════════════════════════════════════════════════════════
#   Total Active Approvals:   12
#   Unlimited Approvals:      3
#   Risky Approvals:          0
#   Unique Spenders:          8
#   Unique Tokens:            10
# ═══════════════════════════════════════════════════════════════════
#
# ┌────────────┬─────────────────────────┬──────────────────┬──────────┐
# │   Token    │         Spender         │    Allowance     │   Risk   │
# ├────────────┼─────────────────────────┼──────────────────┼──────────┤
# │       USDC │ Uniswap V3: Router      │       UNLIMITED  │   UNLIM  │
# │       WETH │ OpenSea: Seaport        │       UNLIMITED  │   UNLIM  │
# │        DAI │ 0x7a250d56...           │         1000.00  │      OK  │
# └────────────┴─────────────────────────┴──────────────────┴──────────┘
```

### Show Only Unlimited Approvals

```bash
# Focus on high-risk unlimited approvals
python wallet_auditor.py approvals 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --unlimited

# Output:
# Found 3 unlimited approval(s):
#
# ┌────────────┬─────────────────────────┬──────────────────┬──────────┐
# │   Token    │         Spender         │    Allowance     │   Risk   │
# ├────────────┼─────────────────────────┼──────────────────┼──────────┤
# │       USDC │ Uniswap V3: Router      │       UNLIMITED  │   UNLIM  │
# │       WETH │ OpenSea: Seaport        │       UNLIMITED  │   UNLIM  │
# │       LINK │ 0x1234abcd...           │       UNLIMITED  │   UNLIM  │
# └────────────┴─────────────────────────┴──────────────────┴──────────┘
```

### Scan Other Chains

```bash
# BSC (Binance Smart Chain)
python wallet_auditor.py approvals 0x1234...abcd --chain bsc

# Polygon
python wallet_auditor.py approvals 0x1234...abcd --chain polygon

# Arbitrum
python wallet_auditor.py approvals 0x1234...abcd --chain arbitrum

# Optimism
python wallet_auditor.py approvals 0x1234...abcd --chain optimism

# Base
python wallet_auditor.py approvals 0x1234...abcd --chain base
```

## Full Security Scan

### Complete Security Analysis

```bash
# Run comprehensive security scan
python wallet_auditor.py scan 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --verbose

# Output:
# === Full Security Scan ===
# Address: 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045
# Chain:   ethereum
#
# Step 1/3: Scanning token approvals...
# ✓ Found 12 active approvals
# Step 2/3: Analyzing transaction history...
# ✓ Analyzed 342 transactions
# Step 3/3: Calculating security score...
# ✓ Security score calculated
#
# ╔═══════════════════════════════════════════════════════════════════╗
# ║                    WALLET SECURITY SCORE                          ║
# ╠═══════════════════════════════════════════════════════════════════╣
# ║                                                                   ║
# ║  Overall Score:  [████████████████····] 82/100                    ║
# ║  Risk Level:     🟢 LOW                                           ║
# ║                                                                   ║
# ╠═══════════════════════════════════════════════════════════════════╣
# ║  Component Scores:                                                ║
# ║    Approvals:     [██████████████······] 70/100                   ║
# ║    Interactions:  [██████████████████··] 90/100                   ║
# ║    Patterns:      [████████████████████] 100/100                  ║
# ║                                                                   ║
# ╚═══════════════════════════════════════════════════════════════════╝
```

## Security Score

### Quick Score Check

```bash
# Get just the security score
python wallet_auditor.py score 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Output:
# ╔═══════════════════════════════════════════════════════════════════╗
# ║                    WALLET SECURITY SCORE                          ║
# ╠═══════════════════════════════════════════════════════════════════╣
# ║                                                                   ║
# ║  Overall Score:  [████████████████····] 82/100                    ║
# ║  Risk Level:     🟢 LOW                                           ║
# ║                                                                   ║
# ╚═══════════════════════════════════════════════════════════════════╝
#
# Quick Summary:
#   Score: 82/100 (LOW)
#   Risk Factors: 2
#   Recommendations: 1
```

### JSON Output for Integration

```bash
# Get score as JSON
python wallet_auditor.py score 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --json

# Output:
# {
#   "total_score": 82,
#   "approval_score": 70,
#   "interaction_score": 90,
#   "pattern_score": 100,
#   "risk_level": "low",
#   "risk_factors": [
#     {
#       "category": "approvals",
#       "severity": "medium",
#       "description": "Many unlimited approvals (3)",
#       "score_impact": -15
#     }
#   ],
#   "recommendations": [...]
# }
```

## Transaction History

### Analyze Recent Activity

```bash
# Default 30-day history
python wallet_auditor.py history 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Output:
# Found 342 transactions in the last 30 days
#
# === Transaction History Analysis ===
#   Total Transactions: 342
#   Unique Contracts:   45
#     Verified:         38
#     Unverified:       7
#     Flagged:          1
#   Total Value Sent:   12.5432 ETH
#   Total Gas Spent:    0.2341 Gwei
#
# === Top Contract Interactions ===
#   1. Uniswap V3: Router (89 txs) [✓]
#   2. OpenSea: Seaport (34 txs) [✓]
#   3. Aave: Pool V3 (28 txs) [✓]
#   4. 0x7a250d56... (15 txs) [✗] 🚨
#   5. Curve: 3pool (12 txs) [✓]
```

### Extended History

```bash
# Analyze 90-day history
python wallet_auditor.py history 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --days 90

# Verbose output with details
python wallet_auditor.py history 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --days 60 --verbose
```

## Revoke Recommendations

### Get Revoke List

```bash
# Get list of approvals that should be revoked
python wallet_auditor.py revoke-list 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Output:
# ═══════════════════════════════════════════════════════════════════
#                    REVOKE RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════
#
#   The following approvals should be reviewed and potentially revoked:
#
#   1. LINK → 0x1234abcd... 🚨 RISKY
#      Token:   0x514910771af9ca656af840dff83e8264ecf986ca
#      Spender: 0x1234abcd1234abcd1234abcd1234abcd1234abcd
#      Amount:  UNLIMITED (max uint256)
#      Risk:    Interaction with flagged contract
#
#   2. UNI → 0x9876fedc...
#      Token:   0x1f9840a85d5af5bf1d1762f925bdaddc4201f984
#      Spender: 0x9876fedc9876fedc9876fedc9876fedc9876fedc
#      Amount:  UNLIMITED (max uint256)
#
#   To revoke, use:
#     - revoke.cash
#     - Etherscan Token Approval Checker
#     - Your wallet's built-in approval manager
#
# ═══════════════════════════════════════════════════════════════════
```

## Full Reports

### Generate Text Report

```bash
# Display full report in terminal
python wallet_auditor.py report 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Save to file
python wallet_auditor.py report 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --output security_report.txt
```

### Generate JSON Report

```bash
# Full JSON report for processing
python wallet_auditor.py report 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --json

# Save JSON to file
python wallet_auditor.py report 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --json --output report.json

# Output structure:
# {
#   "address": "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045",
#   "chain": "ethereum",
#   "security_score": {
#     "total": 82,
#     "approval_score": 70,
#     "interaction_score": 90,
#     "pattern_score": 100,
#     "risk_level": "low"
#   },
#   "approval_summary": {
#     "total": 12,
#     "unlimited": 3,
#     "risky": 0,
#     "unique_spenders": 8,
#     "unique_tokens": 10
#   },
#   "transaction_summary": {...},
#   "risk_factors": [...],
#   "recommendations": [...]
# }
```

## Utility Commands

### List Supported Chains

```bash
python wallet_auditor.py chains

# Output:
# === Supported Chains ===
#
# Chain        Chain ID   Explorer
# -------------------------------------------------------
# ethereum     1          https://etherscan.io
# bsc          56         https://bscscan.com
# polygon      137        https://polygonscan.com
# arbitrum     42161      https://arbiscan.io
# optimism     10         https://optimistic.etherscan.io
# base         8453       https://basescan.org
#
# Use --chain <name> to specify a chain (default: ethereum)
```

### Get Help

```bash
# General help
python wallet_auditor.py --help

# Command-specific help
python wallet_auditor.py approvals --help
python wallet_auditor.py scan --help
python wallet_auditor.py report --help
```

## Real-World Scenarios

### New Wallet Security Check

```bash
# Before using a new DeFi protocol, check your current exposure
python wallet_auditor.py scan 0xYOUR_WALLET --verbose

# After approving, verify the new approval
python wallet_auditor.py approvals 0xYOUR_WALLET --unlimited
```

### Quarterly Security Audit

```bash
# Generate comprehensive quarterly report
python wallet_auditor.py report 0xYOUR_WALLET --output q4_2024_security_audit.txt

# Check 90-day activity
python wallet_auditor.py history 0xYOUR_WALLET --days 90
```

### Cross-Chain Security Review

```bash
# Check all your chain deployments
for chain in ethereum bsc polygon arbitrum optimism base; do
  echo "=== $chain ==="
  python wallet_auditor.py score 0xYOUR_WALLET --chain $chain
done
```

### Automated Monitoring Script

```bash
#!/bin/bash
# security_check.sh - Run daily security check

WALLET="0xYOUR_WALLET"
REPORT_DIR="./security_reports"
DATE=$(date +%Y-%m-%d)

# Create report directory
mkdir -p $REPORT_DIR

# Generate daily report
python wallet_auditor.py report $WALLET --json --output "$REPORT_DIR/report_$DATE.json"

# Check for critical risks
SCORE=$(python wallet_auditor.py score $WALLET --json | jq '.total_score')
if [ "$SCORE" -lt 50 ]; then
  echo "WARNING: Security score below 50! Score: $SCORE"
  # Send alert...
fi
```

### Compare Multiple Wallets

```bash
# Check multiple wallets
WALLETS=(
  "0xWALLET1"
  "0xWALLET2"
  "0xWALLET3"
)

echo "Wallet Security Comparison"
echo "=========================="
for wallet in "${WALLETS[@]}"; do
  echo -n "$wallet: "
  python wallet_auditor.py score $wallet --json | jq -r '.total_score'
done
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
