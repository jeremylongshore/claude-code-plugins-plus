# Account Abstraction Reference

Read this when:

- The user asks about AA modes, sponsorship, or chain defaults.
- `aomi tx sign` returns an AA error and you need to pick a flag.
- The user explicitly requests `4337` or `7702`.

## Execution Model

The CLI uses **auto-detect** by default for EVM transactions. It tries account abstraction first, then falls back according to the requested mode:

| User-side provider configured? | Flag | Result |
|---|---|---|
| Pimlico configured | `--aa-provider pimlico` | Pimlico BYOK (user-side credential) |
| Alchemy configured | (none) | Alchemy BYOK (user-side credential) |
| Nothing configured | (none) | Backend Alchemy proxy if available, otherwise EOA fallback after AA attempts |
| Any | `--aa` / `--aa-provider` / `--aa-mode` | AA with explicit settings; no EOA fallback when `--aa` is set |
| Any | `--eoa` | Direct EOA, skip AA |

With no explicit `--aa`, the current TypeScript CLI signs in this order: preferred AA mode, alternative AA mode, then EOA. With `--aa`, it tries AA modes only and returns a hard error if both fail. The zero-config proxy path is useful, but it is not a guarantee of sponsorship or availability.

## Mode Fallback

When using AA, the CLI tries modes in order:

1. Try preferred mode (current configured default: 7702 on Ethereum, Polygon, Arbitrum, Base, and Optimism).
2. If preferred mode fails, try the alternative mode (7702 ↔ 4337).
3. If both modes fail and `--aa` was not set, try EOA.
4. If `--aa` was set, return an AA-only error with the per-mode failures.

## AA Configuration

AA is configured per-invocation via flags or by credentials the user has configured on their side. There is no persistent AA config file on the skill's side.

Priority chain for AA resolution: **flag > user-side credential > backend proxy/default > EOA fallback when allowed**.

## AA Providers

| Provider | Flag                    | Notes                            |
| -------- | ----------------------- | -------------------------------- |
| Alchemy  | `--aa-provider alchemy` | 4337 (sponsored via gas policy), 7702 (EOA pays gas) |
| Pimlico  | `--aa-provider pimlico` | 4337 (sponsored via dashboard policy) |

Provider selection rules:

- If the user explicitly selects a provider via flag, use it.
- In auto-detect mode, the CLI prefers explicit/user-side provider credentials, then the backend Alchemy proxy path.
- Pimlico is used only when explicitly requested or configured; Alchemy can be direct BYOK or backend-proxied depending on available credentials.

The skill never configures provider credentials itself. If `aomi tx sign` reports missing provider credentials, stop and ask the user to configure them before re-running.

## AA Modes

| Mode   | Flag             | Meaning                          | Gas |
| ------ | ---------------- | -------------------------------- | --- |
| `4337` | `--aa-mode 4337` | Bundler + paymaster UserOperation via smart account. Gas sponsored by paymaster. | Paymaster pays |
| `7702` | `--aa-mode 7702` | Native EIP-7702 type-4 transaction with delegation. EOA signs authorization + sends tx to self. | EOA pays |

**7702 requires the signing EOA to have native gas tokens** (ETH, MATIC, etc.). There is no paymaster/sponsorship for 7702. Use 4337 for gasless execution.

## Default Chain Modes

| Chain    | ID    | Default AA Mode | Supported AA Modes |
| -------- | ----- | --------------- | ------------------ |
| Ethereum | 1     | 7702            | 4337, 7702         |
| Polygon  | 137   | 7702            | 7702, 4337         |
| Arbitrum | 42161 | 7702            | 7702, 4337         |
| Base     | 8453  | 7702            | 7702, 4337         |
| Optimism | 10    | 7702            | 7702, 4337         |

These match the live `aomi chain list` output in CLI v0.1.42 for the chains with displayed AA metadata.

## Sponsorship

Sponsorship is available for **4337 mode only**. 7702 does not support sponsorship. Sponsorship policy is configured on the provider's side — the user's provider account decides whether a given UserOperation is sponsored. Once the user has configured their provider, `aomi tx sign` (with the appropriate AA flags if the user wants an explicit provider) will pick up the active policy automatically.

### Sponsorship in practice (verified against v0.1.42 source behavior)

The "zero-config Alchemy proxy" path is not a guarantee of free gas. Empirically:

- **7702 default on the configured EVM chains**: gas is paid by the EOA. A zero native-gas wallet cannot rely on 7702.
- **4337 sponsorship**: depends on the provider/paymaster policy. The backend proxy path may exist, but the skill must not promise gasless execution without evidence from the user's configured provider.
- **Auto mode**: when AA fails and `--aa` was not set, the CLI can try EOA. This means an apparent AA failure may still require native gas because the final submission path is EOA.

**Practical rule the skill must follow**: before signing on an L2, confirm the EOA has a small amount of native gas on the destination chain (~0.0005 ETH equivalent is enough). If the user is sending USDC-only to an L2 with no native gas, warn them that signing on that L2 will fail unless they:

1. fund the EOA with a tiny amount of native gas on that chain, **or**
2. configure a real BYOK AA provider on their side (Alchemy with a Gas Manager policy attached, or Pimlico with a sponsorship policy on the dashboard — the user sets the credential in their own environment) and pass `--aa --aa-provider alchemy|pimlico --aa-mode 4337` on `aomi tx sign`.

Do not promise the user "AA will pay for gas on L2s" without verifying the user's setup. The default proxy path may silently fall through.

When the CLI emits a viem `insufficient funds for transfer` error, do not re-run with `--eoa` blindly — `--eoa` will also fail if the EOA has 0 gas. Stop and tell the user to fund the destination chain or configure a sponsoring BYOK provider.

## Supported Chains

| Chain         | ID       | AA available? |
| ------------- | -------- | ------------- |
| Ethereum      | 1        | Yes (4337, 7702; default 7702) |
| Polygon       | 137      | Yes (7702, 4337; default 7702) |
| Arbitrum One  | 42161    | Yes (7702, 4337; default 7702) |
| Base          | 8453     | Yes (7702, 4337; default 7702) |
| Optimism      | 10       | Yes (7702, 4337; default 7702) |
| Sepolia       | 11155111 | Chain supported; AA metadata not displayed by `chain list` |
| Linea Mainnet | 59144    | Chain supported; verify provider support before AA |
| Linea Sepolia | 59141    | Chain supported; verify provider support before AA |
| Monad         | 143      | Chain supported; verify provider support before AA |
| Monad Testnet | 10143   | Chain supported; verify provider support before AA |
| Anvil (local) | 31337    | Local chain; prefer `--eoa` unless testing AA explicitly |

For chains without displayed AA metadata, expect provider support to vary. Pass `--eoa` when the user wants a plain EOA signature, or pass explicit AA flags only after confirming the provider supports that chain.

## RPC Guidance By Chain

Use an RPC that matches the pending transaction's chain:

- Ethereum txs → Ethereum RPC
- Polygon txs → Polygon RPC
- Arbitrum txs → Arbitrum RPC
- Base txs → Base RPC
- Optimism txs → Optimism RPC
- Sepolia txs → Sepolia RPC
- Linea txs → Linea RPC
- Monad txs → Monad RPC

Practical rule:

- `--chain` affects the wallet/thread context for chat and request building.
- `--rpc-url` affects where `aomi tx sign` estimates and submits the transaction.
- Treat them as separate controls and keep them aligned with the transaction you are signing.
