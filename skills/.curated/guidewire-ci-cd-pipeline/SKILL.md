---
name: guidewire-ci-cd-pipeline
description: Ship Gosu code and configuration changes through Guidewire Cloud Console deployment slots without breaking running policies — Gosu compile + GUnit + lint gates per PR, config-package promotion dev→UAT→prod, schema-change rollouts with rollback hazards documented, canary deploy for high-risk changes, and the rollback decision tree when a release affects already-bound policies. Use when designing the deploy pipeline for a new InsuranceSuite project, hardening an existing one, or recovering from a bad release. Trigger with "guidewire ci cd", "guidewire deploy", "guidewire promotion", "guidewire slots", "guidewire rollback".
allowed-tools: Read, Write, Edit, Bash(gradle:*), Bash(curl:*), Bash(jq:*), Bash(git:*), Grep, Glob
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - guidewire
  - ci-cd
  - deployment
  - gcc
  - canary
  - rollback
---

# Guidewire CI/CD Pipeline

## Overview

Ship Gosu changes from a developer's branch to production without breaking running policies. Guidewire Cloud Console (GCC) deployment slots are the carrier-side promotion mechanism — `dev` → `uat` → `prod` — with config packages as the unit of promotion. The CI side validates compile, runs GUnit, and packages; the CD side promotes packages through slots with deploy-time gates.

Five production failures this skill prevents:

1. **Bypassed compile/test gates** — a `gradle build` failure on a developer's machine reaches CI as "works on my machine"; CI runs the same gates as a clean clone, fails fast, never lands on a slot.
2. **Promotion without UAT regression** — UW logic change goes dev → prod skipping UAT; the change interacts badly with a product line not exercised in dev; bound policies start showing wrong premium.
3. **Schema change without rollback plan** — a Gosu interface adds a required field; rolling back the deploy is fine, but rolling back the database column requires a separate migration that may have been forgotten.
4. **Canary that isn't a canary** — "canary" deploy serves 100% of traffic immediately because the slot router has no per-slot routing; a real canary needs traffic split, not just a separate slot.
5. **Rollback after policies bound on the new code** — a defective rate-plan deploy bound 200 policies in the 30 minutes before detection; reverting the code does not unbind the policies; they need targeted endorsement-correction or rate adjustment.

## Prerequisites

- A working Guidewire Studio + runServer setup per `guidewire-local-dev-loop`
- GCC tenant with at least three slots (`dev`, `uat`, `prod`) configured for the integration's product line
- A CI runner (GitHub Actions, GitLab CI, Jenkins) with JDK 17 and access to a private artifact registry for config packages
- An age private key (per `guidewire-security-and-rbac`) provisioned to CI for decrypting environment-specific secrets

## Instructions

Build the pipeline in this order. Each step targets one of the five production failures listed in Overview.

### 1. PR-time gates (run on every push)

Three checks, all blocking. The PR cannot merge to `main` if any fails.

```yaml
# .github/workflows/ci.yml
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with: { java-version: 17, distribution: temurin }
      - run: ./gradlew compileGosu                       # gate 1: code compiles
      - run: ./gradlew test                              # gate 2: GUnit passes
      - run: ./gradlew check                             # gate 3: lint + arch + style
```

`compileGosu` catches type errors that Studio's incremental compile sometimes misses. `test` runs the GUnit suite — every UW rule, validation rule, and entity-level Gosu has tests, and CI runs them all in <5 minutes for a normal config zone. `check` includes static analysis (ban on direct DB writes from Gosu, ban on certain plugin patterns, etc.).

### 2. Build the config package on merge to main

```yaml
package:
  needs: validate
  if: github.ref == 'refs/heads/main'
  steps:
    - uses: actions/checkout@v4
    - run: ./gradlew packageConfig
    - run: |
        VERSION=$(git describe --tags --always)
        aws s3 cp build/libs/configuration.zip \
          s3://gw-config-artifacts/${{ github.event.repository.name }}/${VERSION}.zip
```

Config packages are immutable once published. Promotion deploys an existing package to a slot; never modifies it in place. The package name should encode the git SHA so traceability is exact.

### 3. Deploy to dev slot (continuous)

Every merge to `main` deploys to dev automatically. Dev is the first place real Cloud API runtime exercises the change.

```bash
# Promotion API (illustrative — exact GCC API surface varies by tenant)
curl -X POST "$GCC_API/slots/dev/deploy" \
  -H "Authorization: Bearer $GCC_TOKEN" \
  -d '{"package": "configuration-abc1234.zip"}'
```

Wait for deploy to complete (poll status), then run smoke tests against the dev tenant — at minimum, the verification probe from `guidewire-install-auth` and a synthetic FNOL from `guidewire-observability-and-incident-response`. If smoke fails, page the on-call author.

### 4. Promote to UAT with regression gate

UAT is where the product team's regression suite runs. Promotion to UAT is manual (a button in the CD tool) or scheduled (nightly). UAT regression covers:

- A representative submission per active product line (Personal Auto, BOP, Workers Comp, etc.)
- Quote-and-bind for each, asserting expected premium ranges
- A FNOL per loss-cause, asserting the claim opens with the expected exposure shape
- Renewal of a sample in-force policy, asserting the renewal premium falls in expected band

Failed regression blocks promotion to prod automatically. Manual override requires an approver outside the deploying team.

### 5. Canary to prod with traffic split

For high-risk changes (rate plan changes, UW rule logic, payment authorization changes), use a true canary: a separate prod slot serving a percentage of real traffic. GCC supports slot-level traffic splitting on tenants where it's enabled.

```
prod slot:    serves 95% of traffic, runs the previous package
prod-canary:  serves 5%, runs the new package
```

Watch the canary's bind-success-rate, FNOL p99 latency, and 4xx error rate against the main prod slot. After 24h with no SLO breach, ramp to 100% and retire the canary slot.

For low-risk changes (UI text, localization, non-rule Gosu utility classes), skip the canary — single-step promotion to prod is acceptable.

### 6. Rollback decision tree

A bad change is detected. The rollback decision is not "revert the package":

```
Bad change detected in prod
├─ Has any policy been bound or claim opened against the bad code? → check the integration_audit table
│   ├─ NO → revert the package; deploy the previous version; done
│   └─ YES → revert the package AND determine if the bound resources are recoverable
│           ├─ Premium calculation wrong → script-driven rate adjustment endorsements (per affected policy)
│           ├─ Reserve / payment wrong → finance-team-led correction; do not silent-fix
│           └─ FNOL routing wrong → rerun routing logic against affected claims
└─ No policy/claim impact, just operational error (logs noisy, dashboard wrong) → revert and PIR
```

The bound-state recovery path is what makes Guidewire rollbacks different from typical SaaS rollbacks. Code reverts, regulatory state does not.

### 7. Schema-change rollouts (special discipline)

Schema changes (new entity, new column, changed column type) deploy in two phases to retain rollback capability:

```
Phase 1 (deploy):     add new column, code reads-old-or-new, writes-both
Phase 2 (after soak): change code to read-new only, drop old column
```

A 1-week soak between phases gives time to detect issues; a phase-1 rollback drops the not-yet-load-bearing new column. Phase-2 rollback is harder — the old column is gone — so phase 2 only ships when phase 1 has been clean for the full soak.

## Output

A production-grade CI/CD pipeline ships with all of the following:

- Three blocking PR gates: `compileGosu`, `test` (GUnit), `check` (lint/arch).
- An immutable config-package artifact published per merge to main, named by git SHA.
- Continuous dev deployment with smoke-test gate; failures page the merging author.
- Manual UAT promotion with product-team regression suite; failures block prod promotion.
- Canary deploy infrastructure for high-risk changes; bypass path documented for low-risk.
- A rollback runbook that distinguishes "code revert" from "bound-state recovery" and routes accordingly.
- Schema-change two-phase rollout discipline with documented soak times.

## Examples

### Example 1 — GitHub Actions workflow (full pipeline excerpt)

```yaml
name: gw-pipeline
on: { push: { branches: [main] }, pull_request: {} }
jobs:
  validate:    { uses: ./.github/workflows/validate.yml }
  package:     { needs: validate, if: github.ref == 'refs/heads/main', uses: ./.github/workflows/package.yml }
  deploy-dev:  { needs: package, uses: ./.github/workflows/deploy.yml, with: { slot: dev } }
  smoke-dev:   { needs: deploy-dev, uses: ./.github/workflows/smoke.yml, with: { env: dev } }
```

`deploy.yml` and `smoke.yml` are reusable across environments; the `slot` and `env` inputs parameterize.

### Example 2 — UAT regression gate (excerpt)

```yaml
uat-regression:
  runs-on: ubuntu-latest
  steps:
    - run: ./scripts/regress.sh personal-auto      # quote+bind a PA, assert premium in [800,1200]
    - run: ./scripts/regress.sh bop                 # quote+bind a BOP
    - run: ./scripts/regress.sh fnol-auto           # FNOL with vehcollision, assert exposure shape
    - run: ./scripts/regress.sh renewal-pa          # renew a sample PA, assert renewal premium in band
```

### Example 3 — Rollback after bound impact

```bash
# 1. Stop further deploys (block CI)
gh workflow disable gw-pipeline.yml

# 2. Revert the package on prod
curl -X POST "$GCC_API/slots/prod/deploy" -d '{"package": "configuration-abc0001.zip"}'  # previous SHA

# 3. Identify affected policies
psql -c "SELECT resource_id FROM integration_audit 
         WHERE at BETWEEN '2026-04-15T14:00Z' AND '2026-04-15T14:45Z' 
         AND api_path LIKE '%/bind' AND status_code = 200"

# 4. Open finance-team ticket with the policy list and the corrective action
# 5. Re-enable CI only after the corrective endorsements have run
```

## Error Handling

| Symptom | Cause | Solution |
|---|---|---|
| CI passes locally, fails in CI | uncommitted file or environment-specific config | the failing job log shows the file; commit or fix the env |
| `compileGosu` fails on a class that worked locally | Studio incremental compile masked an error | the CI failure is authoritative; fix the code |
| GUnit times out in CI but passes locally | flaky test using ambient sample data | tests must self-fixture; never depend on shared dev DB state |
| Dev deploy succeeds but smoke fails | code change broke a Cloud API contract | the failing smoke check identifies the contract; revert and re-design |
| UAT regression flags a premium drift on a product line | rate plan change interacts with a line not exercised in dev | extend dev test coverage to include that line; do not promote to prod until UAT passes |
| Canary shows elevated 4xx but main prod is clean | the new code introduced a caller-error path | inspect the 4xx response bodies; fix or retire the change |
| Rollback completed but customer-facing system still serves bad data | bound policies on the bad code are unaffected by the rollback | follow the bound-state recovery path; rollback is necessary but not sufficient |
| Schema phase 2 rolled back; old column gone | phase 2 should not ship until phase 1 soak is clean — this scenario means the discipline was bypassed | data recovery from backup; review schema-change discipline |
| `gradle packageConfig` produces a 500MB artifact | unbounded log/build outputs included in the package | tighten the package include patterns; package should be <50MB for a typical config zone |

For deeper coverage (multi-tenant CI fan-out, GitOps with Argo, blue-green deploys, infrastructure-as-code for slot configuration, change-management integration with ITIL ticketing), see [implementation guide](references/implementation-guide.md) and [API reference](references/API_REFERENCE.md).

## See Also

- `guidewire-local-dev-loop` — the same GUnit + sample-data patterns that run in CI
- `guidewire-security-and-rbac` — encrypted secrets that promote with the package, scope assignment per environment
- `guidewire-observability-and-incident-response` — the smoke-test, canary signal, and rollback-decision data this skill references
- `guidewire-migration-and-upgrade` — the larger version-upgrade flow that uses this pipeline as substrate

## Resources

- [GitHub Actions reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows)
- [GCC documentation — deployment slots](https://docs.guidewire.com/cloud/cloudcommons/latest/cloud_console/cc-deployment.html)
- [Google SRE — release engineering](https://sre.google/sre-book/release-engineering/)
- [Schema change patterns — expand-and-contract](https://martinfowler.com/articles/evodb.html#expand-contract)
