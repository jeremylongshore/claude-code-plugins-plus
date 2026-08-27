# Linters, Formatters, and Type Checkers — Static Analysis Sweep

## Contents

[Purpose](#purpose) · [JavaScript / TypeScript](#javascript--typescript) · [Python](#python) · [Rust](#rust) · [Go](#go) · [Ruby](#ruby) · [Java / Kotlin](#java--kotlin) · [PHP](#php) · [Elixir](#elixir) · [.NET](#net) · [C / C++](#c--c) · [Shell / Bash](#shell--bash) · [Dart / Flutter](#dart--flutter) · [Meta-Linters (file-format-specific)](#meta-linters-file-format-specific) · [Enforcement Checklist](#enforcement-checklist) · [Sources](#sources)

## Purpose

Static analysis catches a class of defects that runtime tests can't: style
violations, dead code, potential null-deref, unused imports, missing return
types, unhandled promise rejections, untyped parameters. This reference
catalogs what the skill expects to see per language and how to install +
wire + enforce each tool.

The sweep (Step 5.5) checks three things per language:

1. **Linter** present and configured
2. **Formatter** present and configured (not just installed)
3. **Type checker** present and run in CI (where the language supports it)

Missing tools are flagged P0 (linter, type checker) or P1 (formatter).

## JavaScript / TypeScript

### Linters

| Tool | Signal | Notes |
|---|---|---|
| **ESLint** | `.eslintrc*`, `eslint.config.{js,mjs,cjs}` | Dominant. Flat config (v9+) is preferred. |
| **Biome** | `biome.json` | Rust-based, all-in-one (lint+format). Fast. |
| **oxlint** | `.oxlintrc.json` | Rust-based, ESLint-compatible, 50-100x faster. |
| **standardjs** | `"standard"` in package.json | Opinionated zero-config. Legacy. |

Install + init (Flat config, v9+):

```bash
pnpm add -D eslint @eslint/js typescript-eslint
# eslint.config.js
cat > eslint.config.js <<'EOF'
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommendedTypeChecked,
  { languageOptions: { parserOptions: { projectService: true } } }
);
EOF
```

### Formatters

| Tool | Signal | Notes |
|---|---|---|
| **Prettier** | `.prettierrc*` | Dominant. Opinionated. |
| **Biome** | `biome.json` | If already using Biome as linter. |
| **dprint** | `dprint.json` | Rust-based, pluggable. |

Install:

```bash
pnpm add -D prettier
echo '{}' > .prettierrc  # accept defaults
```

### Type checkers

Only one realistic option: **`tsc --noEmit`** in CI. Never ship without
type checking a TypeScript codebase.

```jsonc
// package.json
"scripts": {
  "typecheck": "tsc --noEmit",
  "lint": "eslint .",
  "format:check": "prettier --check .",
  "format:fix": "prettier --write ."
}
```

## Python

### Linters

| Tool | Signal | Notes |
|---|---|---|
| **Ruff** | `ruff.toml`, `[tool.ruff]` in `pyproject.toml` | **Strongly preferred.** Rust-based, 100x faster than pylint. Replaces flake8, isort, pylint, pyupgrade, pycodestyle, pydocstyle simultaneously. |
| **Pylint** | `.pylintrc`, `pyproject.toml` | Comprehensive but slow. |
| **Flake8** | `.flake8`, `setup.cfg` | Legacy; superseded by Ruff. |
| **Pyflakes** | — | Subset of Flake8. |

Install + init (Ruff):

```bash
uv add --dev ruff
# pyproject.toml
cat >> pyproject.toml <<'EOF'
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "B", "C4", "SIM", "PL", "RUF"]
ignore = []

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101", "PLR2004"]
EOF
ruff check .
```

### Formatters

| Tool | Signal | Notes |
|---|---|---|
| **Ruff format** | `[tool.ruff.format]` | Drop-in Black replacement in same binary. |
| **Black** | `[tool.black]` | Classic. Simple. |
| **isort** | `.isort.cfg`, `pyproject.toml` | Import ordering; Ruff-isort replaces it. |
| **yapf** | `.style.yapf` | Google-flavor. |
| **autopep8** | — | PEP 8-only; less opinionated than Black. |

Install (Ruff format):

```bash
# Already installed above; usage:
ruff format .
ruff format --check .  # CI-safe
```

### Type checkers

| Tool | Signal | Notes |
|---|---|---|
| **mypy** | `mypy.ini`, `[tool.mypy]` | Most common. Strict mode recommended. |
| **pyright** | `pyrightconfig.json` | MS, faster, used by Pylance in VS Code. |
| **pytype** | — | Google. |
| **pyre** | `.pyre_configuration` | Facebook. |

Install (mypy strict):

```bash
uv add --dev mypy
cat >> pyproject.toml <<'EOF'
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
EOF
mypy .
```

### Security static analysis

- **Bandit** — SAST for Python security issues (`bandit -r src/`)
- **Safety** — dep vuln check (`safety check`)
- **pip-audit** — dep vuln check (preferred, uses PyPI advisory DB)

## Rust

Rust's static-analysis story is tight because the compiler does a lot.

### Linter — Clippy

```bash
rustup component add clippy
cargo clippy --all-targets --all-features -- -D warnings
```

Config: `clippy.toml` in repo root for lint-level overrides; `#![deny(...)]`
in `lib.rs`/`main.rs` for crate-wide lints.

### Formatter — rustfmt

```bash
rustup component add rustfmt
cargo fmt --check   # CI
cargo fmt           # fix
```

Config: `rustfmt.toml` for style rules.

### Type checking — `cargo check`

```bash
cargo check --all-targets --all-features
```

### Supply-chain / security

- `cargo audit` — RustSec advisory DB
- `cargo deny` — license + dup + advisory enforcement (recommended)
- `cargo geiger` — unsafe code metrics

## Go

### Linter — golangci-lint (umbrella)

Consolidates: govet, staticcheck, errcheck, ineffassign, unused, revive,
gocritic, gosec, misspell, and many more. The standard in the Go ecosystem.

```bash
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```

Config `.golangci.yml`:

```yaml
linters:
  enable:
    - govet
    - staticcheck
    - errcheck
    - ineffassign
    - unused
    - revive
    - gocritic
    - gosec
    - misspell
    - gofmt
    - goimports
run:
  timeout: 5m
  tests: true
```

### Formatter — gofmt + goimports (+ gofumpt)

```bash
gofmt -l -w .              # enforced via `gofmt -l .` returning empty
goimports -l -w .          # adds import org on top of gofmt
gofumpt -l -w .            # stricter gofmt (optional)
```

### Type checking

Native in `go build`; explicit `go vet ./...` in CI.

### Security

- `govulncheck ./...` — Go vulnerability DB (official)
- `nancy` (Sonatype OSS Index) — optional second opinion

## Ruby

### Linter — RuboCop (or Standard)

```bash
gem install rubocop rubocop-rspec rubocop-performance
rubocop --parallel
```

Config `.rubocop.yml`. Or use `standard` gem for opinionated, zero-config.

### Formatter — RuboCop / rufo

RuboCop auto-corrects formatting. Or `rufo` for formatting-only.

```bash
rubocop -A        # auto-fix
```

### Type checker — Sorbet (RBI) or RBS

- **Sorbet**: `srb tc` — Stripe-backed, runtime + static.
- **RBS + Steep**: official Ruby type system (Ruby 3+).

Install Sorbet:

```bash
gem install sorbet sorbet-runtime
srb init
srb tc
```

### Security

- `brakeman` — Rails SAST
- `bundle-audit` / `bundler-audit` — dep vulns

## Java / Kotlin

### Linters

| Tool | Scope | Signal |
|---|---|---|
| **Checkstyle** | Style | `checkstyle.xml` |
| **PMD** | Bug patterns | `pmd-ruleset.xml` |
| **SpotBugs** | Bytecode analysis | `spotbugs-exclude.xml` |
| **ErrorProne** | Google, build-time | Gradle plugin |
| **Sonar** | All-in-one platform | `sonar-project.properties` |

Gradle snippet:

```kotlin
plugins {
    id("checkstyle")
    id("pmd")
    id("com.github.spotbugs") version "6.x"
    id("net.ltgt.errorprone") version "4.x"
}
```

### Formatter

- **google-java-format** — Google style, strict.
- **Spotless** — wraps google-java-format + ktlint (Kotlin) + others.

```kotlin
plugins { id("com.diffplug.spotless") version "6.x" }
spotless {
    java { googleJavaFormat("1.22.0") }
    kotlin { ktlint("1.3.0") }
}
```

### Type checking — compiler

Built into `javac`/`kotlinc`. CI step: `./gradlew compileJava`.

### Security

- **OWASP Dependency-Check** — `org.owasp.dependencycheck` Gradle plugin
- **Snyk** — freemium SaaS

### Kotlin-specific

- **ktlint** — linter
- **detekt** — static analysis with complexity metrics

## PHP

### Linter + SAST

| Tool | Notes |
|---|---|
| **PHPStan** | Dominant. Level 8+ is gold standard. |
| **Psalm** | Vimeo-backed alternative. |
| **PHP_CodeSniffer** (`phpcs`) | PSR-12 style enforcement. |

Install PHPStan:

```bash
composer require --dev phpstan/phpstan
cat > phpstan.neon <<'EOF'
parameters:
    level: 8
    paths:
        - src
        - tests
EOF
vendor/bin/phpstan analyse
```

### Formatter

- **php-cs-fixer** — dominant
- **phpcbf** — phpcs auto-fix sibling

### Security

- **Roave Security Advisories** — blocks installing insecure deps
- **Psalm-taint-analysis** — taint tracking for security

## Elixir

### Linter — Credo

```elixir
# mix.exs deps
{:credo, "~> 1.7", only: [:dev, :test], runtime: false}
```

```bash
mix credo --strict
```

### Formatter — built-in

```bash
mix format --check-formatted
mix format
```

Config: `.formatter.exs`.

### Type checker — Dialyzer (via dialyxir)

```elixir
{:dialyxir, "~> 1.4", only: [:dev], runtime: false}
```

```bash
mix dialyzer
```

### Security — Sobelow (Phoenix)

```bash
mix sobelow --config
```

## .NET

### Linter

- **Roslyn analyzers** — compiler-integrated, ship with SDK
- **StyleCop.Analyzers** — NuGet, style-focused
- **SonarAnalyzer.CSharp** — Sonar rules as analyzers

### Formatter — `dotnet format`

```bash
dotnet format                 # fix
dotnet format --verify-no-changes   # CI check
```

Config: `.editorconfig` (native .NET reads it).

### Type — compiler

Enforce nullable reference types:

```xml
<PropertyGroup>
  <Nullable>enable</Nullable>
  <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
</PropertyGroup>
```

### Security

```bash
dotnet list package --vulnerable
dotnet list package --deprecated
```

## C / C++

### Linter

- **clang-tidy** — dominant, modern, rule-configurable
- **cppcheck** — alternative, classic

```bash
clang-tidy src/*.cpp -- -Iinclude -std=c++20
```

Config: `.clang-tidy` file in repo root.

### Formatter — clang-format

```bash
clang-format --dry-run --Werror src/*.cpp  # CI
clang-format -i src/*.cpp                  # fix
```

Config: `.clang-format`.

### Static analysis

- **scan-build** (clang) — path-sensitive checker
- **CodeChecker** — wraps clang-tidy + scan-build with web UI
- **PVS-Studio** — commercial
- **Coverity** — commercial

### Runtime sanitizers (build flags)

- **AddressSanitizer** — `-fsanitize=address`
- **UndefinedBehaviorSanitizer** — `-fsanitize=undefined`
- **ThreadSanitizer** — `-fsanitize=thread`
- **MemorySanitizer** — `-fsanitize=memory` (clang only)

Combine in CI: compile + run test suite under ASan+UBSan.

## Shell / Bash

### Linter — ShellCheck (mandatory)

```bash
shellcheck scripts/**/*.sh
```

Catches quoting bugs, `[` vs `[[`, subtle portability issues. **Never
ship a shell script without ShellCheck in CI.**

### Formatter — shfmt

```bash
shfmt -d scripts/       # diff (CI)
shfmt -w scripts/       # write
```

## Dart / Flutter

### Linter — dart analyze + package:lints

```bash
dart analyze
```

Config: `analysis_options.yaml` with `include: package:lints/recommended.yaml`.

### Formatter — `dart format`

```bash
dart format --set-exit-if-changed .    # CI
dart format .                          # fix
```

## Meta-Linters (file-format-specific)

| Tool | Target | Config |
|---|---|---|
| **hadolint** | Dockerfile | `.hadolint.yaml` |
| **yamllint** | YAML | `.yamllint.yaml` |
| **markdownlint** / **markdownlint-cli2** | Markdown | `.markdownlint.json` |
| **Stylelint** | CSS / SCSS | `.stylelintrc` |
| **taplo** | TOML | `taplo.toml` |
| **actionlint** | GitHub Actions YAML | none needed |
| **shellcheck** | Bash (see above) | `.shellcheckrc` |
| **kubeconform** / **kubeval** | K8s manifests | — |
| **cfn-lint** | CloudFormation | `.cfnlintrc` |
| **tflint** | Terraform | `.tflint.hcl` |
| **ansible-lint** | Ansible | `.ansible-lint` |

These are file-type-specific; install as the repo contains relevant files.

## Enforcement Checklist

For each language detected in the repo, the sweep verifies:

- [ ] Linter installed (package manifest)
- [ ] Linter config file present
- [ ] Linter runs in CI with failing exit code
- [ ] Formatter installed
- [ ] Formatter config present (or documented as defaults)
- [ ] `format --check` (non-fixing) in CI
- [ ] Type checker installed (for statically-typed languages)
- [ ] Type check runs in CI with failing exit code
- [ ] Pre-commit hook invokes lint + format on staged files
- [ ] CI does NOT use `continue-on-error: true` on these steps

Missing any of these is a reportable gap.

## Sources

- Airbnb JavaScript Style Guide — github.com/airbnb/javascript
- Google Java Style — google.github.io/styleguide/javaguide.html
- Ruff docs — docs.astral.sh/ruff
- Clippy lints index — rust-lang.github.io/rust-clippy/master/
- golangci-lint docs — golangci-lint.run
- PHPStan levels — phpstan.org/user-guide/rule-levels
- Sorbet docs — sorbet.org/docs
- OWASP SAMM v2, Design — Threat Assessment + Security Requirements.
