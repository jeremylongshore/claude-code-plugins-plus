# Gotchas, Hard Rules, and Security Model

## What You Probably Got Wrong

LLM training data on aomi is stale. These are the most common mistakes the skill is shaped to prevent. Each correction is anchored to current `@aomi-labs/client` v0.1.42 behavior and local TypeScript source.

- **"Aomi is a wallet"** → Aomi is an agent + CLI. It composes calldata and queues a wallet request; the user signs. The CLI does not custody funds, never signs without an explicit `aomi tx sign`, and never broadcasts on its own initiative.

- **"`aomi chat` always queues a transaction"** → Often the first response is a quote, route, or clarifying question. The agent only stages calldata when it has enough context. Always run `aomi tx list` after chat to see what is actually pending — never assume.

- **"Approval and swap are one transaction"** → Most DeFi flows are two-step: `approve` then `supply`/`swap`/`deposit`. Aomi stages them as a batch and `aomi tx simulate tx-1 tx-2` runs them sequentially on a fork so the second step sees the first's state changes. Sign them as a batch, not individually.

- **"Use `--rpc-url` to switch chains"** → `--chain` controls the wallet/thread context (which chain the agent thinks you are on); `--rpc-url` controls where `aomi tx sign` estimates and submits. They are independent. For a cross-chain flow, the queued tx has its own `chain` field — pass `--rpc-url` matching *that* chain when signing.

- **"AA always sponsors gas on L2s"** → The currently displayed AA defaults are 7702 on Ethereum, Polygon, Arbitrum, Base, and Optimism. 7702 spends native gas from the EOA. 4337 can be sponsored only when the selected provider/paymaster policy supports it. If the EOA has 0 native gas on the destination chain, auto mode may still fail after AA attempts because the fallback path is EOA. See [account-abstraction.md → Sponsorship in practice](account-abstraction.md#sponsorship-in-practice-verified-against-v0142-source-behavior).

- **"`--new-session` should always be passed"** → Pass it on the *first* command of a new task. Reusing it mid-task starts a fresh conversation and the agent loses context (e.g. the quote it just gave you). For follow-up confirmations like *"yes, proceed"*, omit `--new-session`.

- **"Failed simulation txs disappear"** → They do not. `aomi tx list` can show older `tx-N` entries from earlier failed attempts alongside the current passing batch. Check the `batch_status` line and only sign txs marked as passing.

- **"7702 and 4337 are interchangeable"** → They are not. 7702 is a native EIP-7702 type-4 transaction with EOA delegation; the EOA pays gas. 4337 is a bundler+paymaster UserOperation; the paymaster can sponsor. Current displayed defaults: 7702 on Ethereum, Polygon, Arbitrum, Base, and Optimism. Use 4337 only when a supported paymaster path is actually configured.

- **"Local key setup still uses the old wallet command"** → The current surface uses `aomi wallet dev-key` for local test keys and `aomi wallet ls` for linked wallet/account policy inspection. Solana local keys use `aomi wallet dev-key --solana <base58-or-json-keypair>` or `--solana-private-key` / `SOLANA_PRIVATE_KEY` for one invocation.

- **"`aomi app list` and `aomi model list` are required preflights"** → These introspection routes are backend-dependent and may return 404 on the public backend. Do not block chat, tx list, simulation, or signing flows just because app/model listing is unavailable.

- **"Drain vectors are aomi-specific"** → They are protocol-specific calldata fields where a malicious prompt could redirect funds (`recipient` in Uniswap, `onBehalfOf` in Aave, `mintRecipient` in CCTP, `_to` in OP-stack bridges). The agent blocks these at simulation time when they do not equal `msg.sender`. The skill's job is to surface the block, not bypass it. Full table in [drain-vectors.md](drain-vectors.md).

## Hard Rules

- Never invent, guess, or derive a credential value. The skill only ever passes through a value the user has explicitly given for a specific action in this turn.
- Never echo a credential value back after it has been used. Confirm the action ("dev key set", "secret `<HANDLE_NAME>` added") without restating the value.
- Setup commands that take a credential (`aomi wallet dev-key <signing-key>`, `aomi secret add NAME=<value>`, flags like `--private-key`) are only run when the user has explicitly asked for that specific setup in this turn and has supplied the value themselves. Do not run them on the skill's own initiative to "prepare" or "fix" something.
- Before running a credential-setup command the user asked for, briefly confirm what will be persisted and where (local CLI state vs. the aomi backend — see [workflows.md → Secret Ingestion](workflows.md#secret-ingestion) for the transmission note), so the user can abort.
- Only call `aomi tx sign` after `aomi tx list` shows a pending `tx-N` the user asked for.
- When starting a new assistant thread, default the first aomi command to `--new-session` unless the user wants to continue an existing thread.
- The signing RPC must match the pending transaction's chain. `--chain` (thread context) and `--rpc-url` (signing transport) are independent — keep them aligned.
- `--aa-provider` and `--aa-mode` are AA-only controls and cannot be used with `--eoa`.

## Security Model

This skill is scoped to the `aomi` CLI. It does not install software, read files outside the aomi state directory, or execute code it generates.

- **Credentials are opaque pass-through.** The skill never fabricates, guesses, or derives a credential value. Values only reach the CLI when the user has handed them over for a specific command in this turn, and they are not echoed or retained.
- **No unsolicited setup.** The skill does not run credential-persisting setup (`aomi wallet dev-key`, `aomi secret add NAME=<value>`) to "prepare" for a task. It runs those commands only when the user explicitly asked, with the value the user supplied.
- **No blind signing.** Multi-step flows (approve → swap, approve → deposit) go through `aomi tx simulate` on a forked chain before `aomi tx sign`. Single-step read operations do not require simulation.
- **User-directed batches only.** `aomi tx sign` can take multiple ids; that is for batches the user has reviewed, not for sweeping a queue.
- **Read-only by default.** Chat, simulation, thread inspection, and app/model/chain introspection do not move funds. Signing is a separate, explicit step the user must ask for.
