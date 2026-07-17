# ADR: BDE Score — MCP Server Architecture and Protocol Choices

**Author:** BDE Score Team
**Date:** 2025-07-17
**Status:** Accepted

## Context

BDE Score needs to serve blockchain deployer evaluation data to AI agents via the Model Context Protocol. The system must support real-time scoring, micropayments for premium data access, regulatory compliance marking, and decentralized discovery — all while remaining lightweight and deployable as an MCP server within the claude-code-plugins-plus-skills marketplace.

The constraints are: (1) the MCP SDK provides the transport layer, (2) blockchain data must be fetched in real time, (3) micropayments must not break the synchronous MCP tool-call pattern, and (4) EU AI Act compliance requires metadata on all AI-generated outputs.

## Decision

We use a hosted MCP server architecture that connects to the production endpoint via the MCP SDK's streaming transport. The server acts as a thin wrapper that routes tool calls to the BDE Score API, which handles blockchain data fetching, scoring computation, and x402 payment verification internally. EU AI Act compliance is enforced as a post-processing layer on all tool responses.

## Alternatives considered

| Alternative | Why rejected |
|-------------|-------------|
| Embedded full-node blockchain indexer | Too heavy for an MCP plugin; would require GB of storage and constant sync |
| REST-only API without MCP transport | Loses native Claude Code integration; MCP provides better tool discovery and streaming |
| Subscription-based pricing model | Excludes casual and low-volume users; x402 micropayments enable pay-per-query with no commitment |

## Consequences

**Positive:**

- Zero local infrastructure required — agents connect directly to the hosted MCP endpoint
- x402 micropayments allow fine-grained billing without subscription lock-in
- EU AI Act compliance is transparent to the user — metadata is automatically attached
- .well-known discovery enables agent-to-agent interoperability without centralized directories

**Negative / accepted tradeoffs:**

- Dependency on the hosted Cloudflare tunnel endpoint introduces a single point of failure for the free tier
- Real-time blockchain data fetching adds latency (~1-5s per query) compared to cached/precomputed scores
- AGPL-3.0 licensing may restrict commercial redistribution without the commercial license

## Tool-permission scope

| Tool | Why it's needed |
|------|----------------|
| `node src/index.js` | Launches the MCP server process for Claude Code integration |
| Network access (HTTPS) | Required to reach the BDE Score production API and Cloudflare MCP endpoint |
| `process.env.BDE_MCP_ENDPOINT` | Allows users to override the endpoint for self-hosted deployments |
