# PRD: BDE Score — Blockchain Deployer Evaluation MCP Server

**Author:** BDE Score Team
**Date:** 2025-07-17
**Status:** Active

## Problem

AI agents interacting with blockchains lack a standardized way to evaluate the reputation and security posture of on-chain deployers before engaging with their smart contracts. Current tooling requires manual investigation across multiple explorers, with no unified scoring, no micropayment support for pay-per-query access, and no compliance with emerging AI transparency regulations (EU AI Act Art.50).

DeFi protocols, DAOs, and autonomous agents face financial risk when interacting with unaudited deployers — and there is no lightweight MCP-native solution to assess deployer trustworthiness in real time.

## Target users

| User | Context | Primary need |
|------|---------|--------------|
| DeFi protocol operators | Evaluating new deployers before integration | Quick risk score and compliance check |
| AI agent developers | Building autonomous on-chain agents | Standardized MCP interface for deployer evaluation |
| Security researchers | Auditing blockchain accounts | Reputation data and behavioral pattern analysis |
| DAO governance participants | Vetting proposals from new deployers | Transparent, reproducible scoring with audit trail |

## Success criteria

1. Agent can retrieve a deployer security score via a single MCP tool call in under 5 seconds
2. EU AI Act Art.50 compliance marking is automatically attached to all generated evaluations
3. x402 micropayment flow completes without breaking the MCP tool call chain
4. .well-known discovery endpoints return valid agent.json, mcp.json, and security.txt responses

## Functional requirements

- **FR-1:** Provide MCP tools for deployer evaluation, security scoring, compliance checking, identity verification, and agent discovery
- **FR-2:** Support x402 HTTP 402 micropayment protocol for pay-per-query access to premium scoring data
- **FR-3:** Automatically mark all AI-generated outputs with EU AI Act Art.50 transparency metadata
- **FR-4:** Expose .well-known discovery endpoints (agent.json, mcp.json, security.txt) per RFC 8615
- **FR-5:** Support W3C DID-based decentralized identity for agent and deployer verification

## Out of scope

- On-chain transaction execution (this is an evaluation/scoring tool, not a wallet or executor)
- Smart contract source code auditing (BDE Score evaluates deployer reputation, not code correctness)
- Off-chain identity verification or KYC processes
