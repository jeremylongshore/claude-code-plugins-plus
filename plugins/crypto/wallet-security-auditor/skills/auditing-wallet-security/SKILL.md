---
name: auditing-wallet-security
description: |
  Audit wallet security by analyzing token approvals, permissions, and transaction patterns.
  Use when checking wallet security, reviewing approvals, or assessing risk exposure.
  Trigger with phrases like "audit wallet", "check approvals", "security scan", or "revoke tokens".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(crypto:wallet-*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Wallet Security Auditor

## Overview

Security analysis tool for cryptocurrency wallets. Scans ERC20 token approvals, analyzes transaction patterns, calculates security risk scores, and provides actionable recommendations to improve wallet security.

**Important**: This is a read-only analysis tool. It does NOT execute transactions, manage private keys, or perform revocations.

## Prerequisites

Before using this skill, ensure you have:
- Python 3.8+ with `requests` library installed
- Optional: `ETHERSCAN_API_KEY` environment variable for higher rate limits
- Network access to blockchain RPC endpoints (public RPCs included)
- Target wallet address (hex format, 0x...)

## Instructions

### 1. List Token Approvals

Scan wallet for all active ERC20 token approvals:

```bash
cd ${CLAUDE_SKILL_DIR}/scripts
python wallet_auditor.py approvals <address> --chain <chain>
```

Options:
- `--chain`: ethereum, bsc, polygon, arbitrum, optimism, base (default: ethereum)
- `--unlimited`: Show only unlimited approvals
- `--verbose`: Detailed output

### 2. Full Security Scan

Comprehensive security analysis including approvals, transaction history, and patterns:

```bash
python wallet_auditor.py scan <address> --verbose
```

Analyzes:
- Active token approvals (unlimited, risky)
- Transaction history patterns
- Contract interactions (verified vs unverified)
- Suspicious activity detection

### 3. Calculate Security Score

Get weighted security risk score (0-100, higher = safer):

```bash
python wallet_auditor.py score <address>
python wallet_auditor.py score <address> --json  # JSON output
```

Score components:
- Approvals (40%): Unlimited, risky, stale approvals
- Interactions (30%): Contract verification, flagged addresses
- Patterns (20%): Transaction frequency, diversity
- Age (10%): Wallet maturity

Risk levels:
- 90-100: SAFE
- 70-89: LOW
- 50-69: MEDIUM
- 30-49: HIGH
- 0-29: CRITICAL

### 4. Analyze Transaction History

Review recent contract interactions and patterns:

```bash
python wallet_auditor.py history <address> --days 30
```

Detects:
- Rapid approval patterns
- Interaction bursts (many contracts in short time)
- High failure rates
- Dust attacks

### 5. Generate Revoke List

Get prioritized list of approvals to revoke:

```bash
python wallet_auditor.py revoke-list <address>
```

Flags:
- Unlimited approvals to unknown contracts
- Risky/flagged spenders
- Stale approvals (>6 months)

### 6. Generate Full Report

Create comprehensive security audit report:

```bash
python wallet_auditor.py report <address> --output report.txt
python wallet_auditor.py report <address> --json  # JSON format
```

### 7. List Supported Chains

```bash
python wallet_auditor.py chains
```

## Output

### Security Score Report
```
╔═══════════════════════════════════════════════════════════════════╗
║                    WALLET SECURITY SCORE                          ║
╠═══════════════════════════════════════════════════════════════════╣
║  Overall Score:  [████████████████····] 82/100                    ║
║  Risk Level:     🟢 LOW                                           ║
╠═══════════════════════════════════════════════════════════════════╣
║  Component Scores:                                                ║
║    Approvals:     [██████████████······] 70/100                   ║
║    Interactions:  [██████████████████··] 90/100                   ║
║    Patterns:      [████████████████████] 100/100                  ║
╚═══════════════════════════════════════════════════════════════════╝
```

### Approval Summary
- Total active approvals count
- Unlimited approvals flagged
- Risky approvals with severity
- Unique spenders and tokens

### Risk Factors
- [CRITICAL] Unlimited approval to unknown contract
- [HIGH] Approval to flagged contract
- [MEDIUM] Many unlimited approvals (>5)
- [LOW] Interaction with unverified contract

### Recommendations
- Priority 1: Revoke risky approvals immediately
- Priority 2: Review unnecessary unlimited approvals
- Priority 3: Audit all approvals periodically

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling:

| Error | Cause | Solution |
|-------|-------|----------|
| Address validation failed | Invalid format | Use 0x + 40 hex characters |
| RPC timeout | Node unresponsive | Retry or use different RPC |
| Rate limited | Too many requests | Add ETHERSCAN_API_KEY |
| No approvals found | Wallet clean | Normal - no action needed |

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

### Quick Security Check
```bash
# Check wallet approvals
python wallet_auditor.py approvals 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Full security scan
python wallet_auditor.py scan 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045 --verbose

# Get security score
python wallet_auditor.py score 0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045

# Check other chains
python wallet_auditor.py approvals 0x... --chain polygon
python wallet_auditor.py approvals 0x... --chain arbitrum
```

### Generate Audit Report
```bash
# Text report
python wallet_auditor.py report 0x... --output security_audit.txt

# JSON for integration
python wallet_auditor.py report 0x... --json --output audit.json
```

## Resources

- **revoke.cash**: Web UI for revoking approvals
- **Etherscan Token Approval Checker**: View/revoke on block explorer
- **Etherscan API**: https://docs.etherscan.io/api-endpoints
- **ERC20 Approval Event**: Topic `0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925`
- **GoPlus Security API**: Additional contract risk data
