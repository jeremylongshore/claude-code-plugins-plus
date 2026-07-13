# Troubleshooting

Read this when a command fails unexpectedly or behaves differently than the workflow predicts.

## Chat / Thread

- If `aomi chat` returns `(no response)`, wait briefly and run `aomi thread status`.
- If `aomi thread status` shows the thread is gone, the local pointer may be stale — retry with `--new-session`.

## Signing

- If AA signing fails, the CLI tries the alternative AA mode automatically. If both modes fail and `--aa` was not set, it can try EOA. Read the console output before retrying manually.
- If AA fails with a credential error, stop and ask the user to check their provider configuration on their side. Do not try to configure it from the skill.
- If a transaction fails on-chain, check the RPC URL, balance, and chain.
- If the signer address differs from the stored thread public key, the CLI updates the thread to the signer address and continues — this is expected, not an error.

## RPC

- `401`, `429`, and generic parameter errors during `aomi tx sign` are usually RPC problems, not transaction-construction problems. Pass a reliable chain-matching public RPC via `--rpc-url`.
- If one or two public RPCs fail for the same chain, stop rotating through random endpoints and ask the user to supply a proper RPC URL for that chain themselves. Do not paste provider-keyed URLs into chat.
- The pending transaction already contains its target chain. If the default RPC is wrong, override with `--rpc-url` for the matching chain.

## Simulation

- If `aomi tx simulate` fails with a revert, read the revert reason. Common causes: expired quote or timestamp (re-chat to get a fresh quote), insufficient token balance, missing prior approval. Do not sign transactions that failed simulation without understanding why.
- If `aomi tx simulate` returns `stateful: false`, the backend could not fork the chain — simulation ran each tx independently via `eth_call`, so state-dependent flows (approve → swap) may show false negatives. Retry, or check that the backend's Anvil instance is running before signing.

## Cross-chain

- When the chat/thread chain (`--chain`) differs from the chain the agent eventually queues a tx for, that's normal — the user may have asked for a cross-chain operation. Sign with `--rpc-url` matching the *queued tx*'s chain, not the thread chain.

## Invocation

- If `aomi: command not found`, the user does not have the global install. Substitute `npx @aomi-labs/client@latest` for `aomi` in every command and retry.
- If `aomi --version` reports a version older than `0.1.42`, advise `npm install -g @aomi-labs/client@latest` (or use `npx @aomi-labs/client@latest …` for one-shot calls) before continuing — older versions may lack flags or Solana/account-auth behavior this skill assumes.

## Quirks observed in current CLI/source

These are not bugs the skill should try to fix — they are CLI behaviors to recognize and route around.

- **`[session] Backend user_state mismatch (non-fatal)` log spam** appears between the prompt and the agent response. These lines are large JSON dumps that look alarming. Ignore them — they are not errors. Look past them for the actual agent response and the `⚡ Wallet request queued: tx-N` line.
- **The active thread pointer can disappear between shell invocations.** If `aomi tx list` returns `No active thread` after a successful chat, run `aomi thread list` to find the thread id (look for `topic` matching what you just asked the agent), then `aomi thread resume <N> > /dev/null && aomi tx list` in the **same** shell call.
- **Stale failed-simulation txs accumulate.** When the agent retries (e.g. Across with expired deadlines), the failed prior attempts stay visible in `aomi tx list`. Match against the `batch_status` metadata: only sign txs whose status reads `Batch [...] passed`. Skip ones tagged `failed at step N: 0x...`.
- **Agent self-heals expired deadlines.** For deadline-bearing routes (Across, Khalani fillers), if simulation reports an expiry, the agent will rebuild the request automatically with fresh deadlines. Do not re-prompt — just check `aomi tx list` for the latest passing batch.
- **`BYOK key set for anthropic: sk-ant-...` echoes the first ~7 characters of the provider key.** This is by design (provider identification, not authentication). Do not try to scrub it from output — it is not a credential leak.
- **Public backend app/model introspection can return 404.** Treat `aomi app list` and `aomi model list` as convenience commands. A 404 there does not prove chat, tx, simulation, or signing is broken.
- **Solana instruction-only pending requests are not fully CLI-signable yet.** The current TypeScript signer reconstructs pending Solana signables when the backend/local pending record includes `unsigned_tx` / `unsignedTx`. Canonical `svm_ixs` without an unsigned tx may be filtered out.

## AA and native gas

If `aomi tx sign` returns `insufficient funds for transfer` from viem, the active path needs native gas from the EOA. See `references/account-abstraction.md#sponsorship-in-practice-verified-against-v0142-source-behavior` for the expected behavior and recovery options. Short version: the EOA needs a small amount of native gas on the destination chain, or the user needs to configure a real BYOK 4337 provider with a sponsorship policy. Do not retry with `--eoa` blindly — that path also requires gas.
