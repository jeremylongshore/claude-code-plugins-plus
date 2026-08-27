# Architecture Constraints — Wall 7

## Contents

[Per-Language Tool Matrix](#section-1-per-language-tool-matrix) · [Standard Rule Pack](#section-2-standard-rule-pack-one-per-language) · [Hash-Pinning Rule Configs](#section-3-hash-pinning-rule-configs) · [AUDIT Flow](#section-4-audit-flow) · [IMPLEMENT Flow](#section-5-implement-flow) · [Remediation — Dependency Inversion](#section-6-remediation--dependency-inversion-not-rule-relaxation) · [Cross-References](#section-7-cross-references) · [Sources](#sources)

> **THE ENGINEER AUTHORS THE RULES. THE AI OBEYS THEM.**
>
> Rule-config files (`.dependency-cruiser.js`, `.importlinter`, `deptrac.yaml`,
> `ArchTest*.java`, etc.) are hash-pinned by `scripts/harness-hash.sh`. Any
> AI diff that modifies them fails CI with `HARNESS_TAMPERED`. On violation,
> the AI must **invert the dependency** or relocate the import — never
> relax the rule.

Wall 7 enforces Clean Architecture's Dependency Rule at build time: source
code dependencies point inward, inner layers know nothing of outer layers.
A test that passes in a module whose imports violate the rule is not worth
much, because the module will fail in production when the outer layer
changes out from under it.

The skill runs two flows against this wall:

- **AUDIT flow**: detect language, invoke the right checker with the
  repo's rule pack, fail the pipeline on any violation.

- **IMPLEMENT flow**: install the language-appropriate checker, emit the
  standard rule pack config (hash-pinned immediately), wire the project
  target and CI job.

---

## Section 1: Per-Language Tool Matrix

| Language | Tool | Config file | Install |
|----------|------|-------------|---------|
| JS/TS | **dependency-cruiser** | `.dependency-cruiser.js` | `npm i -D dependency-cruiser` |
| TS (fluent) | **ArchUnitTS** | `tests/architecture/*.test.ts` | `npm i -D archunit-ts` |
| Python | **import-linter** | `.importlinter` | `pip install import-linter` |
| Java / Kotlin | **ArchUnit** | `src/test/java/ArchitectureTest.java` | Gradle: `com.tngtech.archunit:archunit-junit5` |
| Kotlin (fluent) | **Konsist** | `src/test/kotlin/**/KonsistTest.kt` | Gradle: `com.lemonappdev:konsist` |
| .NET | **NetArchTest** | `test/*.ArchTests.cs` | `dotnet add package NetArchTest.Rules` |
| .NET (fluent) | **ArchUnitNET** | `test/*.ArchTests.cs` | `dotnet add package ArchUnitNET.xUnit` |
| PHP | **deptrac** | `deptrac.yaml` | `composer require --dev qossmic/deptrac` |
| Go | **arch-go** | `arch-go.yml` | `go install github.com/arch-go/arch-go@latest` |
| Go (alt) | **go-cleanarch** | CLI flags | `go install github.com/roblaszczak/go-cleanarch@latest` |
| Rust | `cargo-modules` + allowlist | `arch-rules.toml` (repo convention) | `cargo install cargo-modules` (less mature — flagged honestly) |

Detection order used by the skill:

1. `.dependency-cruiser.js` / `.dependency-cruiser.cjs` → dependency-cruiser
2. `.importlinter` or `[importlinter]` in `pyproject.toml` → import-linter
3. `deptrac.yaml` → deptrac
4. `arch-go.yml` → arch-go
5. Source tree with `ArchUnit` imports → ArchUnit
6. None found → IMPLEMENT mode

---

## Section 2: Standard Rule Pack (one per language)

Every implemented project gets this five-rule pack, transliterated into the
target tool's config language:

1. **No circular dependencies** — any cycle fails the build.
2. **Domain isolation** — `domain/` (or `src/core/`, `lib/core/`) imports
   nothing from `infrastructure/`, `ui/`, or external frameworks.

3. **Test → source one-way** — `tests/` may import `src/`; reverse forbidden.
4. **Dev deps stay dev** — `devDependencies` never imported by production code.
5. **No orphan modules** — every module is reachable from at least one
   entry point (sieves out dead code).

### JS/TS `.dependency-cruiser.js` starter

```javascript
module.exports = {
  forbidden: [
    {
      name: "no-circular",
      severity: "error",
      from: {},
      to: { circular: true },
    },
    {
      name: "domain-no-infrastructure",
      severity: "error",
      from: { path: "^src/domain" },
      to: { path: "^src/(infrastructure|ui|adapters)" },
    },
    {
      name: "domain-no-frameworks",
      severity: "error",
      from: { path: "^src/domain" },
      to: {
        dependencyTypes: ["npm", "npm-dev"],
        pathNot: "^node_modules/(zod|uuid|date-fns)$",
      },
    },
    {
      name: "src-no-tests",
      severity: "error",
      from: { path: "^src" },
      to: { path: "(^|/)tests?/" },
    },
    {
      name: "no-orphans",
      severity: "warn",
      from: {
        orphan: true,
        pathNot: "\\.(d\\.ts|config\\.(js|ts)|spec\\.)",
      },
      to: {},
    },
    {
      name: "prod-no-dev-deps",
      severity: "error",
      from: { path: "^src", pathNot: "\\.spec\\.|\\.test\\." },
      to: { dependencyTypes: ["npm-dev"] },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "tsconfig.json" },
  },
};
```

### Python `.importlinter` starter

```ini
[importlinter]
root_package = myapp

[importlinter:contract:layers]
name = Layered architecture
type = layers
layers =
    myapp.ui
    myapp.application
    myapp.domain
    myapp.infrastructure

[importlinter:contract:domain-pure]
name = Domain imports no frameworks
type = forbidden
source_modules =
    myapp.domain
forbidden_modules =
    django
    flask
    fastapi
    sqlalchemy

[importlinter:contract:tests-one-way]
name = src does not import tests
type = forbidden
source_modules =
    myapp
forbidden_modules =
    tests
```

### PHP `deptrac.yaml` starter

```yaml
deptrac:
  paths:
    - ./src
  layers:
    - name: Domain
      collectors:
        - { type: directory, regex: src/Domain/.* }
    - name: Application
      collectors:
        - { type: directory, regex: src/Application/.* }
    - name: Infrastructure
      collectors:
        - { type: directory, regex: src/Infrastructure/.* }
    - name: UI
      collectors:
        - { type: directory, regex: src/UI/.* }
  ruleset:
    Domain: []
    Application: [Domain]
    Infrastructure: [Application, Domain]
    UI: [Application]
```

### Java ArchUnit starter (`ArchitectureTest.java`)

```java
@AnalyzeClasses(packages = "com.example.app", importOptions = ImportOption.DoNotIncludeTests.class)
class ArchitectureTest {

  @ArchTest
  static final ArchRule no_cycles =
      slices().matching("com.example.app.(*)..").should().beFreeOfCycles();

  @ArchTest
  static final ArchRule domain_isolated =
      noClasses().that().resideInAPackage("..domain..")
          .should().dependOnClassesThat().resideInAnyPackage("..infrastructure..", "..ui..");

  @ArchTest
  static final ArchRule layered =
      layeredArchitecture().consideringAllDependencies()
          .layer("UI").definedBy("..ui..")
          .layer("Application").definedBy("..application..")
          .layer("Domain").definedBy("..domain..")
          .layer("Infrastructure").definedBy("..infrastructure..")
          .whereLayer("UI").mayNotBeAccessedByAnyLayer()
          .whereLayer("Application").mayOnlyBeAccessedByLayers("UI")
          .whereLayer("Domain").mayOnlyBeAccessedByLayers("Application", "Infrastructure")
          .whereLayer("Infrastructure").mayOnlyBeAccessedByLayers("UI", "Application");
}
```

---

## Section 3: Hash-Pinning Rule Configs

The five-rule pack is only meaningful if the config cannot be silently
weakened. The skill hash-pins the following files via
`scripts/harness-hash.sh`:

- `.dependency-cruiser.js` / `.dependency-cruiser.cjs`
- `.importlinter`
- `deptrac.yaml`
- `arch-go.yml`
- `ArchitectureTest.java` (any file matching `*ArchTest*.java` or `*ArchitectureTest*.java`)
- `*ArchTests.cs`

Any byte change to these files without an engineer-initiated `--init` fails
the pipeline with `HARNESS_TAMPERED`. See `scripts/escape-scan.sh` for the
full escape-pattern table.

---

## Section 4: AUDIT Flow

```bash
# Unified command — auto-detects language and dispatches
bash scripts/arch-check.sh

# Example output (dependency-cruiser):
# error no-circular: src/domain/user.ts → src/services/user.ts → src/domain/user.ts
# error domain-no-infrastructure: src/domain/billing.ts → src/infrastructure/stripe.ts
```

### AUDIT report section

```
ARCHITECTURE (Wall 7)
  Tool detected:         dependency-cruiser (v16.3)
  Rule pack hash:        OK (pinned 2026-04-15)
  Rules evaluated:       6
  Violations:            2 (BLOCKING)
    1. domain-no-infrastructure
       src/domain/billing.ts → src/infrastructure/stripe.ts
       Remediation: inject StripeGateway interface, keep domain pure.
    2. no-circular
       auth.ts → session.ts → auth.ts
       Remediation: extract shared type into src/domain/auth-types.ts.
  Proposed dep-inversion patches: 2 (see reports/arch/proposals/)
```

---

## Section 5: IMPLEMENT Flow

When no rule config exists, the skill implements Wall 7:

1. **Detect primary language** — by top-level files (`package.json`,
   `pyproject.toml`, `composer.json`, `go.mod`, `Cargo.toml`, `build.gradle`).

2. **Install the language tool** from Section 1 matrix.
3. **Emit the rule-pack config** from Section 2, tuned to the repo's
   discovered layer names (scan top-level `src/` subdirectories to pick
   `domain/core/app` names).

4. **Initialize the hash manifest** for the new config file:
   `bash scripts/harness-hash.sh --init`.

5. **Wire a project target**:
   - `npm run arch` → `depcruise --validate src/`
   - `make arch` → `lint-imports`
   - `./gradlew archTest`
   - `composer arch` → `vendor/bin/deptrac`
6. **Wire CI job** that runs the target and fails the build on non-zero
   exit.

7. **Report** all proposed files to the engineer for review.

---

## Section 6: Remediation — Dependency Inversion, Not Rule Relaxation

When a violation is detected, the skill proposes one of:

- **Dependency inversion** — the inner layer defines an interface; the
  outer layer implements it. Example: `domain/billing.py` defines
  `PaymentGateway`; `infrastructure/stripe.py` implements it; composition
  wires them together at the edge.

- **Import relocation** — the offending module is in the wrong layer;
  move it.

- **Extract shared type** — for cycles, pull the shared contract into a
  more-inner module that both cycle members depend on.

The skill never proposes:

- Editing the rule config to allow the violation
- Adding inline `depcruise-disable`, `@ArchIgnore`, `ignore_imports`,
  `skip_violations`

- Moving the rule from `error` to `warn`

Those are escape attempts caught by `scripts/escape-scan.sh` at the
REFUSE severity.

### Example proposed diff (Python, dependency inversion)

Before (violates `domain-pure`):

```python
# myapp/domain/billing.py
from myapp.infrastructure.stripe import charge   # VIOLATION

def process_refund(order):
    return charge(-order.total)
```

After:

```python
# myapp/domain/billing.py
from typing import Protocol

class PaymentGateway(Protocol):
    def charge(self, amount: int) -> str: ...

def process_refund(order, gateway: PaymentGateway):
    return gateway.charge(-order.total)

# myapp/infrastructure/stripe.py
from myapp.domain.billing import PaymentGateway

class StripeGateway:
    def charge(self, amount: int) -> str:
        return stripe_client.charge(amount)
```

---

## Section 7: Cross-References

- Wall 1 (acceptance) → `{baseDir}/references/acceptance-tests-gherkin.md`
- Walls 5/6 (CRAP) → `{baseDir}/references/crap-and-complexity.md`
- Remediation → `{baseDir}/references/auto-remediation.md`
- Arch checker → `{baseDir}/scripts/arch-check.sh`
- Hash protocol → `{baseDir}/scripts/harness-hash.sh`
- Escape detection → `{baseDir}/scripts/escape-scan.sh`

---

## Sources

- [Clean Architecture — Dependency Rule](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [dependency-cruiser rules reference](https://github.com/sverweij/dependency-cruiser/blob/main/doc/rules-reference.md)
- [ArchUnit User Guide](https://www.archunit.org/userguide/html/000_Index.html)
- [ArchUnitTS](https://lukasniessen.github.io/ArchUnitTS/)
- [import-linter docs](https://import-linter.readthedocs.io/)
- [deptrac docs](https://qossmic.github.io/deptrac/)
