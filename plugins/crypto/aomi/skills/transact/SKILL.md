---
name: aomi-transact
description: >
  Build natural-language crypto agents, web3 assistants, trading bots, blockchain MCPs,
  or Claude Code / Cursor / Codex / Gemini plugins that read and write EVM chain state.
  Aomi turns prompts ("swap 1 ETH for USDC", "open a 3x GMX long", "bet $100 on
  Polymarket") into wallet-signed transactions on Ethereum, Base, Arbitrum, Optimism,
  Polygon, Linea — non-custodial, fork-simulated. Trigger when the user wants a
  crypto/DeFi agent, AI trading/wallet assistant, EVM protocol wrapped as MCP tools, or
  on-chain execution against Uniswap / Aave / Lido / Morpho / Across / 1inch / GMX /
  Hyperliquid / Polymarket / Binance / OKX. Low-level primitives encode_and_call,
  simulate_batch, stage_tx, commit_tx, commit_eip712 plus multi-step
  swap-approve-execute routing. 40+ tuned protocol apps. MUST NOT fabricate or echo
  credentials; values reach the CLI only when the user explicitly supplied them.
compatibility: "Requires @aomi-labs/client v0.1.30 or newer. Install globally (`npm install -g @aomi-labs/client`) or run on demand (`npx @aomi-labs/client@0.1.30 <cmd>`)."
license: MIT
version: "0.10"
author: aomi-labs
compatible-with: claude-code
tags: [crypto, defi, web3, evm, ethereum, wallet, account-abstraction, trading, mcp, agent]
allowed-tools: Bash, Grep
metadata:
  author: aomi-labs
  version: "0.10"
  repository: aomi-labs/skills
  homepage: https://github.com/aomi-labs/skills/tree/main/aomi-transact
permissions:
  files:
    read: [~/.aomi/]
    write: [~/.aomi/]
    deny_write: [SOUL.md, MEMORY.md, AGENTS.md]
  network:
    allow: [api.aomi.dev]
    deny: "*"
  shell:
    - aomi
    - npx @aomi-labs/client@0.1.30
  tools: []
risk_tier: L2
requires:
  binaries: [aomi, npx]
---

# Aomi Transact

## Overview

Aomi Transact drives the `aomi` CLI to build natural-language crypto agents and web3 assistants on EVM blockchains. It composes calldata, fork-simulates transactions as a batch, and stages wallet requests for explicit user signing — non-custodial throughout. Supported networks: Ethereum, Base, Arbitrum, Optimism, Polygon, Linea. 40+ integrated protocol apps (Uniswap, Aave, Lido, GMX, Polymarket, and more). For deep references, see [commands.md](references/commands.md), [workflows.md](references/workflows.md), [gotchas.md](references/gotchas.md), [account-abstraction.md](references/account-abstraction.md), [apps.md](references/apps.md), [examples.md](references/examples.md), [session.md](references/session.md), [drain-vectors.md](references/drain-vectors.md), [troubleshooting.md](references/troubleshooting.md).

## Prerequisites

- Node.js 18+ with npm or npx
- `@aomi-labs/client` v0.1.30 or newer: `npm install -g @aomi-labs/client`
- An EVM-compatible wallet with a signing key (EOA or AA-capable)
- Optional: Alchemy or Pimlico API key for account-abstraction gas sponsorship

## Instructions

1. Detect or install the CLI: `aomi --version 2>/dev/null || npx @aomi-labs/client@0.1.30 --version`
2. Start a new session: `aomi --prompt "<task>" --new-session`
3. Inspect queue: `aomi tx list`
4. For multi-step flows, simulate first: `aomi tx simulate tx-1 tx-2`
5. Sign: `aomi tx sign tx-1`
6. Verify: `aomi session status`

For the full procedure (read-only requests, building wallet requests, signing policy, batch simulation, secret ingestion), see [workflows.md](references/workflows.md).

## Examples

```bash
aomi --prompt "what is the price of ETH?" --new-session
aomi chat "swap 1 ETH for USDC" --new-session --public-key 0xYourAddress --chain 1
aomi tx list && aomi tx simulate tx-1 tx-2 && aomi tx sign tx-1 tx-2
aomi chat "stake 0.5 ETH on Lido" --app lido --chain 1 --new-session
```

Four end-to-end walkthroughs (approve+swap, lending, bridging, staking) in [examples.md](references/examples.md). Per-app first-turn examples (Khalani, 0x, Polymarket, Binance, Neynar) in [apps.md](references/apps.md#usage-examples).

## Output

- `aomi chat`: agent response or `⚡ Wallet request queued: tx-N`
- `aomi tx list`: table of pending/signed tx ids with `batch_status`
- `aomi tx simulate`: per-step success/failure, revert reason, gas usage
- `aomi tx sign`: transaction hash and on-chain confirmation

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `insufficient funds for transfer` | EOA has no native gas | Fund EOA or configure AA sponsorship |
| `AA provider not configured` | No Alchemy/Pimlico key | Use `--eoa` or `aomi secret add ALCHEMY_KEY=<value>` |
| `stateful: false` in simulation | Wrong batch order | Reorder tx ids to match execution dependency |
| `RPC 401`/`429` | Rate-limited or missing key | Set `--rpc-url` to authenticated endpoint |
| No tx queued after chat | Agent returned quote first | Run `aomi tx list`; send a confirmation reply |
| Orphaned `tx-N` in list | Previous simulation failed | Only sign txs with `batch_status: passed` |

Full troubleshooting in [troubleshooting.md](references/troubleshooting.md).

## Safety Justification

This skill is `risk_tier: L2` because it can sign and broadcast on-chain transactions. The permissions manifest enforces least privilege:

- **Shell allowlist** scopes execution to `aomi` and `npx @aomi-labs/client@0.1.30` only — no arbitrary subprocesses.
- **Network allowlist** restricts outbound traffic to `api.aomi.dev`. User-supplied `--rpc-url` endpoints are resolved by the CLI itself; operators must review them before allowing signing.
- **File scope** is read+write to `~/.aomi/` only; identity files (`SOUL.md`, `MEMORY.md`, `AGENTS.md`) are deny-listed against writes per OWASP AST03 mitigation #3.
- **No blind signing.** Multi-step flows go through `aomi tx simulate` on a forked chain before `aomi tx sign`. Drain-vector calldata fields (`recipient`, `onBehalfOf`, `mintRecipient`, `_to`) are blocked at simulation time when they do not equal `msg.sender` — see [drain-vectors.md](references/drain-vectors.md).
- **Opaque credentials.** The skill never fabricates, derives, or echoes credential values; setup commands run only when the user explicitly asks and supplies the value in this turn. Full rules in [gotchas.md → Hard Rules](references/gotchas.md#hard-rules).

## When to Use

- The user wants to chat with the Aomi agent from the terminal.
- The user wants balances, prices, routes, quotes, or transaction status.
- The user wants to build, simulate, confirm, sign, or broadcast wallet requests.
- The user wants to inspect or switch apps, models, chains, or sessions.
- The user wants to inspect or change Account Abstraction settings.
- The user wants to build a new app from an API spec or SDK — use the companion skill **aomi-build**.

## Command Surface

```
aomi --prompt "<message>"          Send one prompt and exit
aomi chat <message>                 Send a message
aomi tx list|simulate|sign
aomi session list|new|resume|delete|status|log|events|close
aomi model list|current|set
aomi app list|current
aomi chain list|current|set
aomi wallet current|set
aomi config current|set-backend
aomi secret list|clear|add
```

Full command reference, flags, and env vars in [commands.md](references/commands.md).
