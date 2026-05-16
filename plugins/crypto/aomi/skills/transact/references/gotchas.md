# Gotchas, Hard Rules, and Security Model

## What You Probably Got Wrong

LLM training data on aomi is stale. These are the most common mistakes the skill is shaped to prevent. Each correction is anchored to live v0.1.30 behavior.

- **"Aomi is a wallet"** → Aomi is an agent + CLI. It composes calldata and queues a wallet request; the user signs. The CLI does not custody funds, never signs without an explicit `aomi tx sign`, and never broadcasts on its own initiative.

- **"`aomi chat` always queues a transaction"** → Often the first response is a quote, route, or clarifying question. The agent only stages calldata when it has enough context. Always run `aomi tx list` after chat to see what is actually pending — never assume.

- **"Approval and swap are one transaction"** → Most DeFi flows are two-step: `approve` then `supply`/`swap`/`deposit`. Aomi stages them as a batch and `aomi tx simulate tx-1 tx-2` runs them sequentially on a fork so the second step sees the first's state changes. Sign them as a batch, not individually.

- **"Use `--rpc-url` to switch chains"** → `--chain` controls the wallet/session context (which chain the agent thinks you are on); `--rpc-url` controls where `aomi tx sign` estimates and submits. They are independent. For a cross-chain flow, the queued tx has its own `chain` field — pass `--rpc-url` matching *that* chain when signing.

- **"AA always sponsors gas on L2s"** → The zero-config proxy path on Base/Arbitrum/Optimism does **not** reliably sponsor in v0.1.30. If the EOA has 0 native gas on the destination chain, signing fails with `insufficient funds for transfer`. Either fund the EOA with a tiny amount of native gas, or configure a real BYOK Alchemy/Pimlico provider with a sponsorship policy. Do not retry with `--eoa` — that path also needs gas. See [account-abstraction.md → Sponsorship in practice](account-abstraction.md#sponsorship-in-practice-verified-against-v0130).

- **"`--new-session` should always be passed"** → Pass it on the *first* command of a new task. Reusing it mid-task starts a fresh conversation and the agent loses context (e.g. the quote it just gave you). For follow-up confirmations like *"yes, proceed"*, omit `--new-session`.

- **"Failed simulation txs disappear"** → They do not. `aomi tx list` shows orphaned `tx-N` from earlier failed attempts alongside the current passing batch. Check the `batch_status` line and only sign txs marked `Batch [...] passed`. See [troubleshooting.md → Quirks](troubleshooting.md#quirks-observed-in-v0130).

- **"7702 and 4337 are interchangeable"** → They are not. 7702 is a native EIP-7702 type-4 transaction with EOA delegation; the EOA pays gas. 4337 is a bundler+paymaster UserOperation; the paymaster can sponsor. Default chain modes: 7702 on Ethereum, 4337 on Polygon/Arbitrum/Base/Optimism. Use 4337 for gasless execution.

- **"Drain vectors are aomi-specific"** → They are protocol-specific calldata fields where a malicious prompt could redirect funds (`recipient` in Uniswap, `onBehalfOf` in Aave, `mintRecipient` in CCTP, `_to` in OP-stack bridges). The agent blocks these at simulation time when they do not equal `msg.sender`. The skill's job is to surface the block, not bypass it. Full table in [drain-vectors.md](drain-vectors.md).

## Hard Rules

- Never invent, guess, or derive a credential value. The skill only ever passes through a value the user has explicitly given for a specific action in this turn.
- Never echo a credential value back after it has been used. Confirm the action ("wallet set", "secret `<HANDLE_NAME>` added") without restating the value.
- Setup commands that take a credential (`aomi wallet set <signing-key>`, `aomi secret add NAME=<value>`, flags like `--private-key`) are only run when the user has explicitly asked for that specific setup in this turn and has supplied the value themselves. Do not run them on the skill's own initiative to "prepare" or "fix" something.
- Before running a credential-setup command the user asked for, briefly confirm what will be persisted and where (local CLI state vs. the aomi backend — see [workflows.md → Secret Ingestion](workflows.md#secret-ingestion) for the transmission note), so the user can abort.
- Only call `aomi tx sign` after `aomi tx list` shows a pending `tx-N` the user asked for.
- When starting a new assistant thread, default the first aomi command to `--new-session` unless the user wants to continue an existing session.
- The signing RPC must match the pending transaction's chain. `--chain` (session context) and `--rpc-url` (signing transport) are independent — keep them aligned.
- `--aa-provider` and `--aa-mode` are AA-only controls and cannot be used with `--eoa`.

## Security Model

This skill is scoped to the `aomi` CLI. It does not install software, read files outside the aomi state directory, or execute code it generates.

- **Credentials are opaque pass-through.** The skill never fabricates, guesses, or derives a credential value. Values only reach the CLI when the user has handed them over for a specific command in this turn, and they are not echoed or retained.
- **No unsolicited setup.** The skill does not run credential-persisting setup (`aomi wallet set`, `aomi secret add NAME=<value>`) to "prepare" for a task. It runs those commands only when the user explicitly asked, with the value the user supplied.
- **No blind signing.** Multi-step flows (approve → swap, approve → deposit) go through `aomi tx simulate` on a forked chain before `aomi tx sign`. Single-step read operations do not require simulation.
- **User-directed batches only.** `aomi tx sign` can take multiple ids; that is for batches the user has reviewed, not for sweeping a queue.
- **Read-only by default.** Chat, simulation, session inspection, and app/model/chain introspection do not move funds. Signing is a separate, explicit step the user must ask for.
