# @intentsolutions/audit-harness

[![npm](https://img.shields.io/npm/v/@intentsolutions/audit-harness?color=cb3837&logo=npm)](https://www.npmjs.com/package/@intentsolutions/audit-harness)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
[![Provenance](https://img.shields.io/badge/sigstore-provenance-066da5)](https://www.npmjs.com/package/@intentsolutions/audit-harness)

Part of the **[Intent Eval Platform](https://github.com/intent-solutions-io/intent-eval-platform)** — the umbrella mapping the six repos that converge via a shared Evidence Bundle schema.

Deterministic test-enforcement toolkit. Companion to the `audit-tests` and `implement-tests` Claude Code skills — but usable standalone in any repo that wants hash-pinned, escape-scanned, AI-proof quality gates.

## What it is

A small CLI wrapping 6 deterministic scripts:

| Command | Purpose |
|---|---|
| `audit-harness verify` | Verify hash-pinned artifacts haven't changed since `--init` |
| `audit-harness init` | Pin the current state of engineer-owned policy files |
| `audit-harness list` | Show pinned files |
| `audit-harness escape-scan --staged` | Detect AI attempts to lower test thresholds, delete tests, bypass architecture rules |
| `audit-harness arch` | Run language-appropriate architecture-rule checker (dependency-cruiser / import-linter / ArchUnit / deptrac / arch-go) |
| `audit-harness bias` | Count common test-bias patterns |
| `audit-harness gherkin-lint` | Advisory Gherkin quality check |
| `audit-harness crap` | CRAP (Complexity × Coverage) scorer — Python, Go, JS/TS, Rust |

## Install

Pick the install flavor that matches your repo's ecosystem — all three publish the same CLI surface.

**Node / JS / TS** (from npm):

```bash
pnpm add -D @intentsolutions/audit-harness
# or: npm install --save-dev @intentsolutions/audit-harness
# or: yarn add --dev @intentsolutions/audit-harness
```

**Python** (from PyPI):

```bash
pip install intent-audit-harness
# or inside a project venv:
python -m pip install intent-audit-harness
```

**Rust** (from crates.io):

```bash
cargo install intent-audit-harness
```

**Any other language** (Go, Ruby, PHP, Java, .NET, shell, etc.) — vendor the scripts:

```bash
curl -sSL https://raw.githubusercontent.com/jeremylongshore/intent-audit-harness/main/install.sh | bash
```

## Quick usage

### Pre-commit hook (`.husky/pre-commit`)

```bash
#!/usr/bin/env sh
pnpm exec audit-harness escape-scan --staged
pnpm exec audit-harness verify
```

### CI workflow (`.github/workflows/ci.yml`)

```yaml
  containment:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: pnpm/action-setup@v5
      - uses: actions/setup-node@v6
        with: { node-version: '20', cache: 'pnpm' }
      - run: pnpm install --frozen-lockfile
      - run: pnpm exec audit-harness verify
      - run: pnpm exec audit-harness escape-scan --range origin/main..HEAD
```

### Engineer workflow — change a policy threshold

```bash
# 1. Edit tests/TESTING.md to change coverage.line from 80 to 75
# 2. Re-init to accept the change
pnpm exec audit-harness init
# 3. Commit the updated manifest alongside the policy change
git add tests/TESTING.md .harness-hash
git commit -m "chore(test): lower coverage floor to 75"
```

## The containment model

The harness enforces this rule: **policy changes must be conscious, not silent.**

Engineer-owned files (`tests/TESTING.md`, `features/*.feature`, `.dependency-cruiser.cjs`, `stryker.conf.json`, etc.) are hashed into a manifest. Any diff that changes their content without a fresh `audit-harness init` is caught by pre-commit / CI and **REFUSED**.

AI agents remain useful (they can read policy, they can implement within constraints). What they can't do is silently weaken the constraints. That's the entire design.

See `audit-tests/references/philosophy.md` in the companion skill for the full rationale.

## The 7-layer testing taxonomy

This harness sits inside a larger framework:

```text
L7  Acceptance / RTM / Personas / Journeys     ← WHAT are we proving?
L6  E2E / BDD / Visual regression              ← User-level guarantees
L5  Perf / Security (SAST/DAST) / A11y / Chaos ← Non-functional
L4  Integration / Contract / Migration         ← Infrastructure wiring
L3  Unit + Coverage + Mutation + Arch + CRAP   ← Code-level correctness  ← audit-harness lives here
L2  Static analysis / Lint / Types / Secrets   ← Read-only scanning
L1  Git hooks / CI enforcement                 ← The cheapest gate       ← audit-harness enables this
```

The harness commands serve L1 (escape-scan in pre-commit + CI) and L3 (CRAP, architecture, bias, hash-pin).

## Exit codes

Important for CI scripting:

| Exit | Command | Meaning |
|---|---|---|
| 0 | any | Clean |
| 1 | escape-scan | CHALLENGE — requires engineer-approved comment |
| 2 | verify | `HARNESS_TAMPERED` — pinned file changed |
| 2 | escape-scan | REFUSE — pipeline halted |
| 3 | verify | No manifest (fresh repo, not an error) |

## Language support

Most scripts are language-agnostic (shell + regex). CRAP has per-language backends:

| Language | CRAP | Arch | Notes |
|---|---|---|---|
| Python | radon + coverage.py | import-linter | full support |
| JS/TS | complexity-report + c8 | dependency-cruiser | full support |
| Go | gocyclo + go test -cover | arch-go | full support |
| Rust | rust-code-analysis + tarpaulin | (custom) | coverage integration pending |
| Java/Kotlin | — | ArchUnit | via language-native tooling |
| .NET | — | ArchUnitNET | via language-native tooling |
| PHP | — | deptrac | via language-native tooling |

## License

Apache 2.0 — see [LICENSE](./LICENSE) and [NOTICE](./NOTICE).

**Note:** versions `0.x` shipped under the MIT license. Starting with `v1.0.0`, the project is licensed under Apache 2.0. Existing `0.x` releases on npm remain available under their original MIT terms; new releases (`>= 1.0.0`) are Apache 2.0.

## Related

- [`audit-tests` Claude Code skill](https://github.com/jeremylongshore/intent-audit-harness#related) — diagnostic pipeline that uses this harness
- [`implement-tests` Claude Code skill](https://github.com/jeremylongshore/intent-audit-harness#related) — filesystem-mutating installer that installs this harness as part of L1/L3 setup

## Versioning

SemVer. Breaking changes to the CLI surface bump major; new commands bump minor; bug fixes bump patch.

## Contributing

This is infrastructure code. Changes need to be conservative. Before opening a PR:

1. Read `audit-tests/references/philosophy.md` (in the companion skill) to understand the escape-grammar design
2. Run `bash scripts/escape-scan.sh --staged` on your own diff — yes, the harness tests itself
3. Add test cases if you're adding a new pattern to escape-scan or a new command to the CLI
