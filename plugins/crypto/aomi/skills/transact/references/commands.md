# Command Reference

Full command surface for the `aomi` CLI (or `npx @aomi-labs/client@0.1.30` equivalent). The skill invokes read forms freely; `set`/mutating forms only when the user explicitly asks.

## Chat

```bash
aomi --prompt "<message>"                              # one-shot send and exit
aomi chat "<message>" --new-session
aomi chat "<message>" --verbose                        # stream tool calls and agent output
aomi chat "<message>" --model <rig>
aomi chat "<message>" --public-key 0xUserAddress --chain 1
aomi chat "<message>" --app khalani --chain 137
```

- Quote the message.
- On the first command in a new assistant thread, prefer `--new-session`.
- Pass `--public-key` on the first wallet-aware message.
- Use `--app`, `--model`, `--chain` to change the active context for the next request.

## Transactions

```bash
aomi tx list                                           # pending/signed requests
aomi tx simulate <id> [<id> ...]                       # dry-run a batch on a fork
aomi tx sign <id> [<id> ...]                           # sign and submit
```

## Sessions

```bash
aomi session list                                      # local sessions with topic + pending count
aomi session new
aomi session resume <id>                               # set active pointer
aomi session delete <id>                               # remove (check no pending txs first)
aomi session status                                    # current session summary
aomi session log                                       # replay conversation + tool output
aomi session events                                    # raw backend system events
aomi session close                                     # clear active pointer; next chat starts fresh
```

Selectors accept the backend session id, `session-N`, or `N`.

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
aomi model set <rig>                                   # persist model for current session
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
aomi wallet current                                    # configured address only, no credential
aomi wallet set <signing-key>                          # user-directed; user supplies key
aomi config current                                    # backend URL
aomi config set-backend <url>                          # repoint CLI at a different backend
```

`aomi wallet set` persists a signing key under `AOMI_STATE_DIR`. After running, confirm with the derived address — never repeat the key value back.

## Flags and Env Vars

Flags override environment variables.

| Flag            | Default                | Purpose                                                   |
| --------------- | ---------------------- | --------------------------------------------------------- |
| `--backend-url` | `https://api.aomi.dev` | Backend URL                                               |
| `--api-key`     | none                   | API key for non-default apps (user-supplied)              |
| `--app`         | `default`              | Backend app                                               |
| `--model`       | backend default        | Session model                                             |
| `--new-session` | off                    | Create a fresh active session for this command            |
| `--public-key`  | none                   | Wallet address for chat/session context                   |
| `--rpc-url`     | chain RPC default      | RPC override for signing                                  |
| `--chain`       | none                   | Active wallet chain (inherits session chain if unset)     |
| `--eoa`         | off                    | Force plain EOA, skip AA (sign-only)                      |
| `--aa`          | off                    | Force AA, error if provider not configured (sign-only)    |
| `--aa-provider` | auto-detect            | `alchemy` \| `pimlico` (sign-only)                        |
| `--aa-mode`     | chain default          | `4337` \| `7702` (sign-only)                              |

| Env Var           | Default   | Purpose                                |
| ----------------- | --------- | -------------------------------------- |
| `AOMI_STATE_DIR`  | `~/.aomi` | Root directory for local session state |
| `AOMI_CONFIG_DIR` | `~/.aomi` | Root directory for persistent config   |

## Config Rules

- Signing keys must be 0x-prefixed hex. Configuring them is a user action, not a skill action.
- `--aa-provider` and `--aa-mode` cannot be used with `--eoa`.
- The default signing RPC is one URL. For chain switching, pass `--rpc-url` on `aomi tx sign` with a chain-matching public RPC.
- In auto-detect mode, the CLI falls back to a zero-config AA path when no provider is configured.

For account-abstraction details (modes, providers, sponsorship, chain defaults), see [account-abstraction.md](account-abstraction.md).
