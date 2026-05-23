# PRD: Wallet Security Auditor

## Summary

**One-liner**: Audit wallet security by analyzing approvals, permissions, and transaction patterns
**Domain**: Cryptocurrency / Security
**Users**: DeFi users, Traders, Security researchers

## Problem Statement

Wallet security is often overlooked until funds are stolen. Users need tools to audit their token approvals, identify risky contract interactions, and detect potential security issues before they become exploits.

## User Stories

1. As a DeFi user, I want to see all my token approvals so that I can revoke unnecessary or risky permissions.

2. As a trader, I want to analyze a wallet's transaction history so that I can identify suspicious patterns before interacting with it.

3. As a security researcher, I want to check contract interactions for a wallet so that I can assess its risk profile.

4. As a user, I want to generate a security score for my wallet so that I know my overall risk exposure.

## Functional Requirements

- REQ-1: List all ERC20 token approvals for a wallet
- REQ-2: Calculate security risk score based on multiple factors
- REQ-3: Identify interactions with known risky contracts
- REQ-4: Analyze transaction patterns for suspicious activity
- REQ-5: Support multiple chains (Ethereum, BSC, Polygon, etc.)
- REQ-6: Provide actionable recommendations for improving security

## API Integrations

- **RPC Endpoints**: On-chain approval and transaction data
- **Block Explorer APIs**: Etherscan, BSCScan for verified contract info
- **Security APIs**: Token sniffer, GoPlus for contract risk data
- **Revoke.cash API**: Known malicious contracts database

## Success Metrics

- Activation triggers correctly on security-related queries
- Approval data accurate and up-to-date
- Risk score correlates with known security incidents
- Recommendations are actionable and specific

## Non-Goals

- Executing revoke transactions (read-only analysis)
- Private key management or signing
- Real-time monitoring/alerting
- Wallet recovery services
