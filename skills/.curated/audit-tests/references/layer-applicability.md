# Layer Applicability Matrix

Given a repo classification, which of the 7 taxonomy layers does `audit-tests` enable, and which does it waive? The engineer can override in `tests/TESTING.md` under `## Classification`.

---

## Classification signals (detected by `test-discovery-agent`)

| Signal | Classification |
|---|---|
| `package.json` with React/Vue/Svelte/SolidJS/Next/Nuxt in deps | **frontend** |
| HTTP server + OpenAPI/Swagger spec or framework (FastAPI, Express, Gin, Fastify, Spring, Rails API, ASP.NET Core) | **service / api** |
| Binary entry point (`bin/*`, `cmd/*`, `#!/usr/bin/env ...` CLI), no HTTP server | **cli** |
| Published package manifest (`"private": false` in npm, uploaded to PyPI/crates.io, `gemspec`, `.nuspec`) and no application entry | **library** |
| C / C++ project (`Makefile`, `CMakeLists.txt`, `.c`/`.cpp`) and no higher-level app framework | **embedded** |
| Monorepo signals (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `rush.json`, `packages/*/package.json`) | **monorepo** — classify each package independently |
| Regulated compliance markers (HIPAA, SOX, PCI declared in `README.md` / `SECURITY.md`, Compliance: ...) | **regulated** (overlay — escalates gate severity) |

Multiple signals can apply; pick the strongest (service > frontend > cli > library). Engineer override in `TESTING.md` always wins.

---

## Applicable-layer matrix

Legend: ✅ required · ⭕ recommended · ⚠ conditional · ❌ waived by default

| Classification | L1 Hooks | L2 Static | L3 Unit | L4 Integ | L4 Contract | L4 Migration | L5 Perf | L5 Sec | L5 A11y | L5 Chaos | L6 E2E | L6 Smoke | L6 Visual | L7 UAT |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| service / api | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⭕ | ✅ | ❌ | ⭕ | ❌ | ⭕ | ❌ | ⭕ |
| frontend | ✅ | ✅ | ✅ | ⭕ | ⚠* | ❌ | ⚠ | ⭕ | ✅ | ❌ | ✅ | ✅ | ⭕ | ⭕ |
| cli | ✅ | ✅ | ✅ | ⭕ | ❌ | ❌ | ❌ | ⭕ | ❌ | ❌ | ❌ | ✅ | ❌ | ⭕ |
| library | ✅ | ✅ | ✅ (+ strong PBT) | ⭕ | ⚠** | ❌ | ⭕ | ⭕ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| embedded (C/C++) | ✅ | ✅ (+sanitizers) | ✅ (+ fuzz + memory) | ⚠ | ❌ | ❌ | ⭕ | ⭕ | ❌ | ⭕ | ❌ | ⭕ | ❌ | ⭕ |
| regulated (overlay) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ⭕ | ⭕ | ⭕ | ✅ | ⚠ | ✅ |
| monorepo | per-package | per-package | per-package | per-package | per-package | per-package | per-package | per-package | per-package | per-package | per-package | per-package | per-package | per-package |

\* frontend ↔ backend contract tests (Pact consumer-side) if the repo talks to an internal API under contract.
\** library contract tests if the library publishes a documented wire protocol (SDK clients).

---

## Severity gates

Each cell interpreted by `taxonomy-mapper-agent` as follows:

| Symbol | Gate behavior when absent or failing |
|---|---|
| ✅ | **P0** — blocks audit. Handoff to `implement-tests` with this layer in the `install_order`. |
| ⭕ | **P1** — advisory. Listed in audit report; does not block. Engineer can promote to ✅ in `TESTING.md`. |
| ⚠ | **P1 conditional** — inspected, but only fires P0/P1 if a sibling signal detected (e.g. `⚠*` frontend contract tests fire P0 only if internal-API call-sites exist in source). |
| ❌ | Skipped. Not written to gap list. Appears in `TESTING.md` under `Waived layers:` with the classification rationale. |

**Regulated overlay** applied when any of the following appear in the repo root: `HIPAA`, `SOX`, `PCI-DSS`, `SOC2`, `GDPR`, `FedRAMP` tags in README/SECURITY. Overlay promotes all ⭕ to ✅ for security-related layers (L2, L4-contract, L5-sec, L7-UAT) and escalates any uncovered `SHOULD` requirement in `RTM.md` to P0 blocking.

---

## Monorepo handling

For each package under `packages/*`, `apps/*`, `services/*` (or whatever the workspace config declares):

1. Run classification on the package root (its own `package.json` / `pyproject.toml`).
2. Produce one `tests/TESTING.md` at `<package>/tests/TESTING.md`.
3. Aggregate audit results into a single repo-root `TEST_AUDIT.md` with per-package sections.
4. Handoff payload to `implement-tests` is per-package; `scaffold-architect-agent` may parallelize installs across packages if no shared-config conflicts exist (e.g., root-level `.eslintrc` shared by all packages → install once, symlink).

---

## Override mechanism

Engineer edits the `## Classification` section of `tests/TESTING.md`:

```markdown
## Classification (policy)
Repo type: service
Primary language(s): python, typescript
Applicable layers: L1, L2, L3, L4-integration, L4-contract, L5-sec, L6-smoke
Waived layers: L5-a11y (no UI), L7-UAT (product team owns in separate tool)
```

Policy section is hash-pinned. Any AI-proposed edit is caught by `escape-scan.sh` and REFUSED unless preceded by engineer-initiated `harness-hash.sh --init`.
