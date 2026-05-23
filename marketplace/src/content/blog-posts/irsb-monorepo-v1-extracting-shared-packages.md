---
title: "IRSB Monorepo v1.0.0: Extracting Shared Packages and Unifying a Blockchain Platform"
description: "How I extracted @irsb/kms-signer and @irsb/types into shared packages, unified a blockchain platform under one monorepo, dealt with port conflicts, and split CI tests for 3x faster runs."
date: "2026-02-16"
tags: ["monorepo", "typescript", "blockchain", "npm-packages", "architecture", "ci-cd"]
featured: false
---
## Why a Monorepo

IRSB (Intent Receipts & Solver Bonds) is an on-chain guardrails system for AI agents. The protocol enforces spending limits, records execution receipts on-chain, and monitors agent behavior through a watchtower service. By February 2026, the project had grown to 37 Solidity contracts, a TypeScript solver, a watchtower with 12 internal packages, a Python agent service, and a new Envio HyperIndex indexer.

All of these lived in separate repositories. The solver imported types from the protocol SDK. The watchtower duplicated the same KMS signing logic. The indexer needed contract addresses from a shared constants file that existed in three different places.

The monorepo migration was overdue.

## Extracting Shared Packages

Two pieces of code were duplicated across services: the KMS signer and the type definitions.

### @irsb/kms-signer

The solver and watchtower both needed to sign transactions with Google Cloud KMS. Both had their own implementation. Both had slightly different APIs.

The extracted package defines a `Signer` interface with two implementations:

```typescript
// packages/kms-signer/src/signer.ts
export interface Signer {
  signTransaction(tx: TransactionRequest): Promise<SignedTransaction>;
  signMessage(message: SignableMessage): Promise<Hex>;
  signTypedData(data: TypedData): Promise<Hex>;
  isHealthy(): Promise<boolean>;
}
```

`GcpKmsSigner` handles production signing through Google Cloud KMS. `LocalPrivateKeySigner` handles development and testing with a local private key. Both implement the same interface, so services don't care which signer they're using.

### @irsb/types

Contract addresses, chain constants, and TypeScript type definitions were scattered across services. The extracted package centralizes everything:

```typescript
// packages/types/src/contracts.ts
export const CONTRACTS = {
  SolverRegistry: '0xB6ab964832808E49635fF82D1996D6a888ecB745',
  IntentReceiptHub: '0xD66A1e880AA3939CA066a9EA1dD37ad3d01D977c',
  DisputeModule: '0x144DfEcB57B08471e2A75E78fc0d2A74A89DB79D',
  // ... 8 more contracts on Sepolia (chain 11155111)
} as const;

export const MINIMUM_BOND = '0.1';        // ETH
export const CHALLENGE_WINDOW = 3600;      // 1 hour in seconds
export const WITHDRAWAL_COOLDOWN = 604800; // 7 days in seconds
```

Plus `ReceiptStatus`, `DisputeState`, `SolverStatus`, and `IrsbActionType` — all the union types that multiple services need to agree on. One source of truth instead of three.

## Scoped npm Naming

The package naming was a mess. The solver was `@intent-solutions-io/irsb-solver`. The watchtower used `@irsb-watchtower/*` for its nested packages. The protocol SDK was just `irsb`.

Everything got renamed to the `@irsb/*` scope:

| Before | After |
|--------|-------|
| `@intent-solutions-io/irsb-solver` | `@irsb/solver` |
| `irsb-watchtower` | `@irsb/watchtower` |
| `irsb` | `@irsb/sdk` |
| `irsb-x402` | `@irsb/x402` |

All workspace references updated to `workspace:*` protocol. Every `import` statement across the codebase refactored. 20 files changed — mostly mechanical, but one wrong import path and the build breaks.

## Envio HyperIndex Integration

The indexer was the reason the monorepo migration became urgent. IRSB needed real-time event indexing across all 8 contracts (41 events total), and the Envio HyperIndex service needed access to contract ABIs, addresses, and type definitions that already existed in other parts of the project.

The indexer service lives at `services/indexer/` and indexes events across all deployed contracts into a GraphQL API:

- **SolverRegistry**: Registration, bonding, slashing events
- **IntentReceiptHub**: Receipt submission, verification
- **DisputeModule**: Dispute lifecycle (opened, evidence submitted, resolved)
- **X402Facilitator**: Payment channel events
- **WalletDelegate, IdentityRegistry, SpendLimitEnforcer, NonceEnforcer**: Supporting contract events

Testing uses `vitest` with Envio's `MockDb` — no Docker required for unit tests. Development mode starts PostgreSQL + Hasura + the indexer via a `dev.sh` script that manages the container lifecycle.

## Port Conflict Resolution

This is the kind of problem that wastes half a day and teaches you nothing except "check your ports."

The development server had three things competing for two ports:

- System PostgreSQL already on port 5433
- Caddy reverse proxy on port 8080
- Envio indexer needs PostgreSQL (default 5432) and Hasura (default 8080)

The fix: environment variable overrides in `.env`:

```bash
ENVIO_PG_PORT=5434        # Envio PostgreSQL (avoids system PG on 5433)
HASURA_EXTERNAL_PORT=8082 # Hasura GraphQL (avoids Caddy on 8080)
```

The `codegen` script symlinks `.env` into the `generated/` directory so docker-compose picks up the overrides. Not elegant, but explicit and documented.

## CI Optimization: Split Tests for 3x Speed

The protocol CI was running a single `forge test` job with three passes: full tests with verbose traces, coverage check (running the full suite again), and gas report (running it a third time). With 10,000 fuzz runs per test, this took 45+ minutes.

The restructured pipeline runs four parallel jobs:

1. **Unit & Integration** — Standard 256 fuzz runs, excludes fuzz/ and invariant/ directories
2. **Fuzz Tests** — 10,000 runs with CI profile, matches only `test/fuzz/*`
3. **Invariant Tests** — 10,000 runs with CI profile, matches only `test/invariants/*`
4. **Coverage** — Separate job, 80% threshold, non-blocking on test results

```yaml
# Fuzz tests with CI profile (10k runs)
- name: Run fuzz tests
  env:
    FOUNDRY_PROFILE: ci
  run: forge test --match-path "test/fuzz/*"
```

Key changes: removed `-vvv` verbose output (massive with 10k runs), eliminated the gas report step (third redundant full-suite run), and moved coverage to its own parallel job. Estimated improvement: 45 minutes down to 15-20 minutes.

The TypeScript CI runs separately: `pnpm build`, `vitest`, typecheck, lint. Python agents get their own workflow with `pytest` and `ruff`. Indexer CI runs Envio codegen and vitest with the `ENVIO_API_TOKEN` secret. Four CI pipelines for four languages — each fast, each independent.

## The README Overhaul and AI Agent Pivot

The README went from a protocol-focused document to an AI agent positioning piece. The new tagline: "On-Chain Guardrails for AI Agents" (replacing "Intent Receipts & Solver Bonds").

The centerpiece is a gap analysis table comparing IRSB against six frameworks (AgentKit, ElizaOS, Olas, Virtuals, Brian AI, Safe). The question it answers: "Every major framework gives agents wallet access. None answer: what happens when the agent overspends?"

IRSB's answer is three layers: policy enforcement (EIP-7702 + 5 enforcers), execution receipts (cryptographic proof of what happened), and automated monitoring (watchtower). The README includes Mermaid sequence diagrams, architecture flowcharts, a roadmap Gantt chart, and collapsible sections for defense patterns and research highlights.

## BUSL-1.1 Licensing

The license changed from MIT to Business Source License 1.1. The parameters:

- **Change Date**: February 17, 2029 (3 years)
- **Change License**: Converts to MIT automatically
- **Permitted**: Testing, development, research, academic use, public testnet deployment, integration into your own application
- **Prohibited**: Repackaging as a competing commercial on-chain policy enforcement service

This mirrors what Moat, Perception, and git-with-intent all moved to in the same period. The pattern: source-available during the commercial window, fully open-source afterward. It protects against someone cloning the project and selling a hosted version while we're still building the business.

## What I Learned

**Extract packages at two duplications, not three.** The KMS signer was duplicated in solver and watchtower. I should have extracted it when the watchtower copied it from the solver. Waiting until the indexer needed it too meant more refactoring work.

**Scoped npm naming matters early.** Renaming 20 files of imports is tedious but safe when you have TypeScript strict mode catching every broken reference. Doing this rename at 100 packages instead of 30 would be genuinely painful.

**Port conflicts are documentation problems.** The ports themselves are trivial to remap. The real fix is documenting the conflict in `.env.example` so the next developer doesn't spend 30 minutes figuring out why Hasura won't start.

**Split CI by test type, not by language.** Fuzz tests with 10,000 runs don't belong in the same job as unit tests with 256 runs. Different test types have different performance profiles and different failure modes. Parallel jobs with focused scopes give faster feedback and clearer signal.
