# Workflows

End-to-end operational procedures. Use the CLI as one-shot commands — each `aomi` call starts, runs, and exits. Conversation history lives on the backend; local session data lives under `AOMI_STATE_DIR` or `~/.aomi`.

## Quick Start

Run once at the start of a session:

```bash
aomi --version 2>/dev/null || npx @aomi-labs/client@0.1.30 --version
aomi --prompt "hello" --new-session
aomi session status 2>/dev/null || echo "no session"
```

Expected: `aomi --version` prints `0.1.30` or newer. If older, run `npm install -g @aomi-labs/client@latest`.

## Default Workflow

1. Chat with the agent.
2. If the agent asks whether to proceed, reply with a short confirmation in the same session.
3. Review pending requests with `aomi tx list`.
4. For multi-step batches, run `aomi tx simulate tx-1 tx-2 …` before signing.
5. Sign with `aomi tx sign <id>`.
6. Verify with `aomi tx list`, `aomi session log`, or `aomi session status`.

The CLI output is the source of truth. If you do not see `Wallet request queued: tx-N`, there is nothing to sign yet. For a scriptable wrapper, see [../templates/aomi-workflow.sh](../templates/aomi-workflow.sh).

## Read-Only Requests

Use when the user does not need signing:

```bash
aomi --prompt "<message>" --new-session
aomi chat "<message>" --verbose
aomi tx list
aomi session log
aomi session status
aomi --version
aomi app list
aomi app current
aomi chain list
aomi session list
aomi session resume <id>
```

For chain-specific requests, prefer `--chain <id>` on the command itself. Use `AOMI_CHAIN_ID=<id>` only when multiple consecutive commands should stay on the same chain.

## Building Wallet Requests

Give the agent the task plus wallet address and chain on the first turn:

```bash
aomi chat "swap 1 ETH for USDC" --new-session --public-key 0xUserAddress --chain 1
aomi chat "swap 1 POL for USDC on Polygon" --app khalani --chain 137
```

A chat response does not always queue a transaction immediately — the agent may return a quote or route first and ask whether to proceed. Keep the same session and reply with a short confirmation message. Only move to `aomi tx sign` after a wallet request is queued. Confirm with `aomi tx list`.

Queued request:

```
⚡ Wallet request queued: tx-1
   to:    0x...
   value: 1000000000000000000
   chain: 1
Run `aomi tx list` to see pending transactions, `aomi tx sign <id>` to sign.
```

For per-app first-turn examples (Khalani, 0x, Polymarket, Binance, Neynar), see [apps.md](apps.md#usage-examples).

## Batch Simulation

Use `aomi tx simulate` to dry-run pending transactions before signing. Simulation runs each tx sequentially on a forked chain so state-dependent flows (approve → swap) are validated as a batch.

```bash
aomi tx simulate tx-1
aomi tx simulate tx-1 tx-2
```

Response:

```
Simulation result:
  Batch success: true
  Stateful: true
  Total gas: 147821

  Step 1 — approve USDC
    success: true
    gas_used: 46000
  Step 2 — swap on Uniswap
    success: true
    gas_used: 101821
```

**Always simulate multi-step flows** before signing. **Optional** for single independent txs (simple ETH transfer, standalone swap with no prior approval). **Skip** for read-only operations or when `aomi tx list` shows nothing. If simulation fails at step N, read the revert reason before retrying — do not blindly re-sign.

Full simulation-and-signing walkthrough on a multi-step batch in [examples.md](examples.md#1-approve--swap).

## Signing Policy

- Default: `aomi tx sign <tx-id> [<tx-id> ...]` — AA-first via the zero-config Alchemy proxy; falls through to BYOK if Alchemy or Pimlico is configured.
- `--eoa` skips AA entirely.
- `--aa-provider` or `--aa-mode` force AA mode; incompatible with `--eoa`.
- **Mode fallback**: when AA is used, the CLI tries the preferred mode (7702 on Ethereum, 4337 on L2s). If it fails, tries the alternative. If both fail, returns an error suggesting `--eoa`.

```bash
aomi tx sign tx-1                                     # default: zero-config AA
aomi tx sign tx-1 --eoa                               # force EOA
aomi tx sign tx-1 --aa-provider pimlico --aa-mode 4337
```

Signing rules that always apply:

- `aomi tx sign` handles both transaction requests and EIP-712 typed-data signatures. Batch signing is supported for transactions only, not EIP-712.
- A single `--rpc-url` override cannot be used for a mixed-chain multi-sign request.
- The pending transaction already contains its target chain — pass `--rpc-url` matching that chain if the default RPC is wrong.

If signing fails because credentials are missing, stop and ask the user to configure them — do not try to set them from the skill.

## Secret Ingestion

Two paths, depending on who is driving.

**Inspect** (skill-driven, always safe):

```bash
aomi secret list                                       # handle names only, never raw values
aomi secret clear                                      # drop all configured secrets
```

**Add** (user-driven): when the user explicitly asks to configure a credential and supplies the value in this turn:

```bash
aomi secret add NAME=<value> [NAME=<value> ...]
```

Before doing so, warn about the trust boundary (below) so the user can abort. Do not initiate ingestion. Do not paraphrase the user's request into a new credential. Do not repeat the value back — confirm with the handle name only.

**Trust boundary.** `aomi secret add` transmits each credential value to the aomi backend and stores a handle locally. The backend — not just the user's machine — becomes a trust boundary. If the user prefers the value to stay entirely local, advise them to export it in their shell environment and let the CLI read it from there.

## Session And Storage

A session is split across two stores: the **backend** holds the conversation transcript and tool calls; the **local disk** (`$AOMI_STATE_DIR` or `~/.aomi/`) holds lookup keys, pending/signed tx state, and secret handle names. `aomi tx list` reads local; `aomi session log` reads backend.

```bash
aomi session list
aomi session resume <id>
aomi session delete <id>
aomi session close
```

Full layout (`~/.aomi/sessions/session-N.json`, `active-session.txt`), the local-vs-backend split, lifecycle rules for `--new-session` vs `resume`, and cleanup hygiene in [session.md](session.md).
