# Command Reference

Full command surface for the TypeScript `aomi` CLI (or `npx @aomi-labs/client@latest` equivalent), verified against `@aomi-labs/client` v0.1.42. The skill invokes read forms freely; `set`/mutating forms only when the user explicitly asks.

## Chat

```bash
aomi chat "<message>"                                  # one-shot send and exit
aomi --prompt "<message>"                              # root-level compatibility form
aomi chat "<message>" --new-session
aomi chat "<message>" --verbose                        # stream tool calls and agent output
aomi chat "<message>" --model <rig>
aomi chat "<message>" --public-key 0xUserAddress --chain 1
aomi chat "<message>" --app khalani --chain 137
aomi chat "<message>" --account-bearer "$AOMI_ACCOUNT_BEARER"
```

- Quote the message.
- On the first command in a new assistant thread, prefer `--new-session`.
- Pass `--public-key` on the first wallet-aware message.
- Use `--app`, `--model`, `--chain` to change the active context for the next request.

## Transactions

```bash
aomi tx list                                           # pending/signed requests
aomi tx simulate <id> [<id> ...] [--cluster devnet]     # dry-run a batch on a fork / cluster
aomi tx sign <id> [<id> ...] [--cluster devnet]         # sign and submit
```

## Threads

```bash
aomi thread list                                       # local threads with topic + pending count
aomi thread new
aomi thread resume <id>                                # set active pointer
aomi thread delete <id>                                # remove (check no pending txs first)
aomi thread status                                     # current thread summary
aomi thread log                                        # replay conversation + tool output
aomi thread events                                     # raw backend system events
aomi thread close                                      # clear active pointer; next chat starts fresh
```

Selectors accept the backend thread id, `thread-N`, or `N`.

## Secrets

```bash
aomi secret list                                       # handle names only, no values
aomi secret clear                                      # drop all configured secrets
aomi secret add NAME=<value> [NAME=...]                # user-directed only (see workflows.md)
```

## Apps and Models

```bash
aomi app list
aomi app current
aomi model list
aomi model current
aomi model set <rig>                                   # persist model for current thread
```

`aomi chat --model <rig> "<message>"` applies a model for one turn without persisting it. Pick an app per turn with `--app <name>` or `AOMI_APP=<name>`. The installed set is dynamic — confirm with `aomi app list`. Full catalog and per-app credential requirements in [apps.md](apps.md).

## Chain

```bash
aomi chain list
aomi chain current
aomi chain set <id>                                    # only when user asked to change default
```

## Wallet and Config

```bash
aomi wallet ls                                         # linked wallets, providers, signing policy, grants
aomi wallet ls --provider privy                        # filter linked wallets by provider
aomi wallet dev-key <signing-key>                      # user-directed EVM 0x key
aomi wallet dev-key --solana <base58-or-json-keypair>  # user-directed Solana keypair
aomi wallet set-mode <address> <autonomous|human_sync|denied>
aomi login                                             # browser auth URL, mint account bearer
aomi login --provider privy --evm                      # request an EVM provider wallet
aomi login --provider privy --solana                   # request a Solana provider wallet
aomi logout
aomi account                                           # inspect authenticated account and linked methods
aomi config current                                    # backend URL
aomi config set-backend <url>                          # repoint CLI at a different backend
```

`aomi wallet dev-key` persists local signing material under `AOMI_STATE_DIR`. After running, confirm with the derived address or Solana public key — never repeat the key value back. Every linked wallet has a signing policy: `autonomous`, `human_sync`, or `denied`. `aomi wallet set-mode` changes a policy via signed EIP-712 challenge and commit; grants toward `autonomous` must be signed by that wallet's own key.

## Cron

```bash
aomi cron ls                                           # scheduled thread jobs
aomi cron show <id>                                    # inspect one scheduled thread
aomi cron cancel <id>                                  # cancel one scheduled thread
```

## Deploy

```bash
aomi deploy --activation-token "$AOMI_DEPLOY_TOKEN" --app-source-id <id>
```

The TypeScript deploy command is a portal/app-source deployment surface and uses `AOMI_DEPLOY_TOKEN`. Do not confuse it with the Rust `aomi-build deploy` flow, which uses `AOMI_APP_ACTIVATION_TOKEN`.

## Flags and Env Vars

Flags override environment variables.

| Flag            | Default                | Purpose                                                   |
| --------------- | ---------------------- | --------------------------------------------------------- |
| `--backend-url` | `https://api.aomi.dev` | Backend URL                                               |
| `--api-key`     | none                   | API key for non-default apps (user-supplied)              |
| `--account-bearer` | `AOMI_ACCOUNT_BEARER` | Account-bound auth bearer                               |
| `--account-provider` | deprecated         | Legacy provider exchange; prefer `--account-bearer`       |
| `--account-provider-token` | deprecated   | Legacy provider token; prefer `--account-bearer`          |
| `--app`         | `default`              | Backend app                                               |
| `--model`       | backend default        | Thread model                                              |
| `--new-session` | off                    | Create a fresh active thread for this command             |
| `--public-key`  | none                   | Wallet address for chat/thread context                    |
| `--private-key` | `PRIVATE_KEY`          | EVM signing key for this invocation                       |
| `--solana-private-key` | `SOLANA_PRIVATE_KEY` | Solana signing key for this invocation                |
| `--rpc-url`     | chain RPC default      | RPC override for signing                                  |
| `--chain`       | none                   | Active wallet chain (inherits thread chain if unset)      |
| `--cluster`     | `AOMI_SOLANA_CLUSTER`  | Solana cluster (`mainnet-beta`, `devnet`, `testnet`, or CAIP-2) |
| `--eoa`         | off                    | Force plain EOA, skip AA (sign-only)                      |
| `--aa`          | off                    | Force AA, error if provider not configured (sign-only)    |
| `--aa-provider` | auto-detect            | `alchemy` \| `pimlico` (sign-only)                        |
| `--aa-mode`     | chain default          | `4337` \| `7702` (sign-only)                              |

| Env Var           | Default   | Purpose                                |
| ----------------- | --------- | -------------------------------------- |
| `AOMI_STATE_DIR`  | `~/.aomi` | Root directory for local thread state |
| `AOMI_CONFIG_DIR` | `~/.aomi` | Root directory for persistent config   |
| `AOMI_ACCOUNT_BEARER` | none | Account auth bearer minted by login or supplied by user |
| `AOMI_CHAIN_ID` | none | Default active chain |
| `CHAIN_RPC_URL` | none | Signing RPC override |
| `PRIVATE_KEY` | none | EVM signing key |
| `SOLANA_PRIVATE_KEY` | none | Solana signing key |
| `AOMI_SOLANA_CLUSTER` | none | Default Solana cluster |

## Config Rules

- EVM signing keys must be 0x-prefixed hex. Solana signing keys are base58 or JSON keypairs. Configuring either is a user action, not a skill action.
- `--aa-provider` and `--aa-mode` cannot be used with `--eoa`.
- The default signing RPC is one URL. For chain switching, pass `--rpc-url` on `aomi tx sign` with a chain-matching public RPC.
- In auto-detect mode, the CLI tries AA first for EVM transactions and can fall back to EOA when AA fails unless `--aa` was explicitly requested.
- Solana signing currently materializes legacy pending `solana_sign` requests with unsigned transactions; canonical instruction-only `svm_ixs` requests may not appear as CLI-signable pending txs yet.

For account-abstraction details (modes, providers, sponsorship, chain defaults), see [account-abstraction.md](account-abstraction.md).
