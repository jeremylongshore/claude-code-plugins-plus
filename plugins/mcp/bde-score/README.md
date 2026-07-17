# BDE Score

**Blockchain Deployer Evaluation Score — MCP Server for on-chain security scoring, x402 micropayments, and EU AI Act compliance.**

![Version](https://img.shields.io/badge/version-1.0.3-blue.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0-green.svg)

## Overview

BDE Score is an MCP (Model Context Protocol) server that provides blockchain deployer evaluation and security scoring capabilities. It enables AI agents to assess the reputation, security posture, and compliance status of on-chain accounts and smart contract deployers in real time.

**Key Features:**

- 🔐 **On-Chain Security Scoring** — Real-time reputation and risk analysis for blockchain deployers
- 💰 **x402 Micropayment Protocol** — Pay-per-query access with HTTP 402 native integration
- 🇪🇺 **EU AI Act Art.50 Compliance** — AI-generated content transparency marking and disclosure
- 🌐 **.well-known Discovery** — Standardized agent discovery via agent.json, mcp.json, and security.txt
- 🆔 **Decentralized Identity** — W3C DID-based agent identity and verification
- 📊 **Deployer Reputation Analysis** — Historical behavior scoring, pattern detection, and risk grading
- 🔍 **Compliance Checking** — Automated regulatory and policy compliance verification

## What's Included

This plugin provides MCP tools for blockchain deployer evaluation:

| Tool | Description |
|------|-------------|
| `evaluate_deployer` | Assess a deployer's on-chain reputation and security score |
| `check_compliance` | Verify EU AI Act Art.50 and regulatory compliance |
| `get_security_score` | Retrieve real-time security scoring for an address |
| `verify_identity` | Validate W3C DID-based decentralized identity |
| `discover_agent` | Query .well-known endpoints for agent discovery |

## MCP Endpoint

The BDE Score MCP server is available as a hosted service:

```
https://lauderdale-pads-fossil-shot.trycloudflare.com/mcp
```

## Installation

### 1. Install Dependencies

```bash
cd plugins/mcp/bde-score
npm install
```

### 2. Configure MCP Server

Add to your Claude Code MCP configuration file (`~/.claude/mcp_config.json`):

```json
{
  "mcpServers": {
    "bde-score": {
      "command": "node",
      "args": [
        "/absolute/path/to/plugins/mcp/bde-score/src/index.js"
      ]
    }
  }
}
```

**Important:** Replace `/absolute/path/to` with your actual installation path.

Alternatively, connect directly to the hosted endpoint:

```json
{
  "mcpServers": {
    "bde-score": {
      "url": "https://lauderdale-pads-fossil-shot.trycloudflare.com/mcp"
    }
  }
}
```

### 3. Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BDE_MCP_ENDPOINT` | Override the production MCP endpoint | `https://lauderdale-pads-fossil-shot.trycloudflare.com/mcp` |

## Links

- **GitHub:** [hbhqq9/bde-score](https://github.com/hbhqq9/bde-score)
- **Landing Page:** [hbhqq9.github.io/bde-score](https://hbhqq9.github.io/bde-score/)
- **License:** AGPL-3.0 + Commercial (dual license)

## Compliance

- EU AI Act Art.50 — AI-generated content transparency
- x402 Payment Required — HTTP-native micropayments
- W3C DID — Decentralized identifier standard
- .well-known URI — RFC 8615 discovery protocol
