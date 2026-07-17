#!/usr/bin/env node
/**
 * BDE Score MCP Server
 * Blockchain Deployer Evaluation — Security Scoring — x402 Micropayments
 *
 * This plugin connects to the BDE Score production MCP endpoint.
 * For the full server implementation, see: https://github.com/hbhqq9/bde-score
 *
 * Features:
 *   - On-chain deployer security scoring
 *   - x402 micropayment protocol integration
 *   - EU AI Act Art.50 transparency compliance
 *   - .well-known discovery protocol (agent.json, mcp.json, security.txt)
 *   - W3C DID decentralized identity
 *
 * License: AGPL-3.0 + Commercial (dual license)
 */

// Production MCP endpoint
const MCP_ENDPOINT = process.env.BDE_MCP_ENDPOINT || 'https://lauderdale-pads-fossil-shot.trycloudflare.com/mcp';

console.log(`BDE Score MCP Server — connecting to ${MCP_ENDPOINT}`);
console.log('For documentation: https://hbhqq9.github.io/bde-score/');
console.log('Source: https://github.com/hbhqq9/bde-score');
