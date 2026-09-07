# Requirements Traceability, Personas, and User Journeys (Meta-Audit Layer)

Three artifacts that sit *above* the 7-layer taxonomy and ask **"are the tests proving the right things?"** rather than "do the tests pass?". They don't add a layer; they audit the alignment between stated requirements, declared users, observable journeys, and test coverage.

| Artifact | File | Purpose |
|---|---|---|
| Requirements Traceability Matrix | `tests/RTM.md` | Every requirement has ≥1 test; every test links to ≥1 requirement |
| User personas | `tests/PERSONAS.md` | Each declared persona has coverage of their key flows |
| User journeys | `tests/JOURNEYS.md` | End-to-end user flows with step-by-step test mapping |

Applicable repo types: per the matrix in `layer-applicability.md` §3.4 — mandatory for service/frontend/regulated, optional for cli/library.

---

## 1. RTM.md — Requirements Traceability Matrix

### MoSCoW tags (required column)

| Tag | Meaning | Gate behavior if uncovered |
|---|---|---|
| `MUST` | Core product value or legal/safety. Payment auth, security boundaries, data integrity, SLA contracts. | **P0 — blocks audit, triggers handoff to implement-tests** |
| `SHOULD` | Important for quality; product works without it. Error messages, retries, performance above baseline. | P1 — advisory |
| `COULD` | Nice-to-have. Usability polish, rare edge cases, optional integrations. | P2 — logged only |
| `WON'T` | Explicitly out of scope this iteration. Kept to prevent re-surfacing. | Excluded from coverage math |

### Schema

```markdown
# Requirements Traceability Matrix — <repo>
<!-- Managed by rtm-builder-agent. Engineer-edited MoSCoW overrides preserved. -->

| Req ID | MoSCoW | Source | Description | Layers | Test Files | Status |
|---|---|---|---|---|---|---|
| REQ-001 | MUST | features/premium.feature | Premium users get 15% discount | L3, L6, L7 | tests/premium/checkout_test.py, features/premium.feature:12 | ✓ Covered |
| REQ-002 | MUST | docs/ADR-0004.md | API calls auth-gated | L3, L4 | (none) | ✗ **P0 BLOCK** |
| REQ-003 | SHOULD | features/retry.feature | Retry transient 5xx with backoff | L3, L4 | (none) | ⚠ P1 advisory |
| REQ-004 | COULD | docs/PROD-tooltips.md | Tooltip on hover over currency field | L6 | (none) | P2 logged |
| REQ-005 | WON'T | docs/BACKLOG-v2.md | Bulk CSV export | — | — | Excluded |
| REQ-006 | — | (none) | — | L3 | tests/utils/legacy_formatter_test.py | ⚠ Orphaned test |
```

### Sources of requirements (extracted by `rtm-builder-agent`)

| Source | Default MoSCoW |
|---|---|
| `features/*.feature` — each Scenario → one REQ | MUST |
| `docs/ADR-*.md` — each "## Decision" section → one REQ | MUST |
| `docs/000-docs/*-PROD-*.md` — product requirement docs per doc-filing standard | SHOULD |
| Engineer-declared `REQ-*.md` files | MoSCoW required in front-matter; no default |
| Commit messages tagged `refs REQ-*` | COULD |

### MoSCoW assignment precedence

1. **Explicit tag in source.** Gherkin `@must` / `@should` / `@could` / `@wont` scenario tags. ADR front-matter `MoSCoW: MUST`. Product-doc front-matter `priority: must`.
2. **Source-document default** (see table above).
3. **Engineer override in RTM.md** — once the engineer edits a MoSCoW tag, that edit wins across audits. The RTM file is hash-pinned; `escape-scan.sh` REFUSES any AI-proposed downgrade of a `MUST` to a weaker tier.
4. **Inference of last resort** — if none of the above, tagged `SHOULD` with an advisory warning in `TEST_AUDIT.md`.

### Escape-scan patterns specific to RTM

| Pattern | Response |
|---|---|
| Lowering a `MUST` to any weaker tier in `RTM.md` | REFUSE (hash-pinned) |
| Changing a `WON'T` tag without engineer-approved commit note | CHALLENGE |
| Deleting a `MUST` row from `RTM.md` | REFUSE |
| Adding a new `WON'T` to hide an uncovered `MUST` | CHALLENGE — reviewed as a policy edit |

### Orphaned tests

A test file that does not reference any `REQ-*` ID (in a docstring, pytest marker, scenario tag, or dedicated sidecar) is **orphaned**. Always advisory (P1) — orphans may be useful regression tests the engineer wants to keep, but they indicate untracked intent.

---

## 2. PERSONAS.md — User persona coverage

### Schema

```markdown
# Personas — <repo>

## premium-customer
Tier: paid
Permissions: checkout-discount, priority-support, export-data
Key flows: checkout, upgrade-payment, cancel-subscription, export
Test coverage:
  - checkout: features/premium-checkout.feature, tests/checkout/premium_test.py ✓
  - upgrade-payment: (none) ✗
  - cancel-subscription: features/cancellation.feature ✓
  - export: tests/export/premium_export_test.py ✓
Coverage: 3/4 flows (75%) — BELOW THRESHOLD

## free-tier
Tier: free
Permissions: checkout, limited-export
Key flows: checkout, upgrade-cta
Test coverage:
  - checkout: tests/checkout/free_test.py ✓
  - upgrade-cta: e2e/upgrade_cta_spec.ts ✓
Coverage: 2/2 flows (100%)

## admin
Tier: internal
Permissions: all + audit-log + user-impersonation
Key flows: user-lookup, impersonate, audit-read, billing-override
Test coverage:
  - user-lookup: tests/admin/lookup_test.py ✓
  - impersonate: (none) ✗
  - audit-read: tests/admin/audit_test.py ✓
  - billing-override: (none) ✗
Coverage: 2/4 flows (50%) — BELOW THRESHOLD (admin is critical — engineer review)
```

### Threshold

Default: 80% of declared flows must have ≥1 test. Override in `tests/TESTING.md`:

```markdown
## Thresholds (policy, hash-pinned)
personas.flow_coverage_min: 80
personas.critical_flow_coverage_min: 100  # applies to personas tagged critical
```

Fires P1 when below threshold; P0 when a critical-tagged persona has an uncovered flow marked MUST in RTM.

---

## 3. JOURNEYS.md — End-to-end user journey mapping

### Schema

```markdown
# User Journeys — <repo>

## Journey: free-to-premium-conversion
Personas: free-tier → premium-customer
Trigger: user clicks "Upgrade" on quota-exceeded modal
Linked RTM: REQ-001 (premium discount), REQ-017 (webhook tier update)

| # | Step | Layer | Test file | Status |
|---|---|---|---|---|
| 1 | Click upgrade CTA | L6 | e2e/upgrade_flow.spec.ts:12 | ✓ |
| 2 | Land on pricing page | L6 | e2e/upgrade_flow.spec.ts:28 | ✓ |
| 3 | Select plan | L6 | e2e/upgrade_flow.spec.ts:45 | ✓ |
| 4 | Stripe checkout | L4 (mocked) | tests/billing/stripe_test.py | ⚠ Mocked only |
| 5 | Webhook → tier change | L4 | tests/webhooks/stripe_webhook_test.py | ✓ |
| 6 | Confirmation email | L4 | (none) | ✗ |
| 7 | Dashboard reflects new tier | L6 | e2e/upgrade_flow.spec.ts:78 | ✓ |

Coverage: 5/7 steps fully tested (71%).
Gap: confirmation email not tested; Stripe integration mocked only (no contract test).
```

### Threshold

Default: 85% of steps across all journeys must have a linked test. Critical journeys (flagged `critical: true` in the journey header) require 100%.

Gap severity mirrors the RTM MoSCoW of the linked requirements.

---

## Agent responsibilities

| Agent | Runs | Produces / updates |
|---|---|---|
| `rtm-builder-agent` | In audit-tests, every run | Full RTM.md rebuild; preserves engineer MoSCoW overrides; flags orphans + uncovered |
| `persona-coverage-agent` | In audit-tests, every run | Per-persona coverage block in PERSONAS.md; computes % |
| `journey-mapper-agent` | In audit-tests, every run | Per-journey step-by-step table in JOURNEYS.md; flags untested steps |
| `rtm-scaffolder-agent` | In implement-tests, first install only | Generates initial RTM.md / PERSONAS.md / JOURNEYS.md templates from detected artifacts |

### Handoff fields (audit-tests → implement-tests)

When audit finds uncovered MUSTs, the handoff payload includes:

```json
{
  "rtm_gaps": [
    {"req_id": "REQ-002", "moscow": "MUST", "source": "docs/ADR-0004.md",
     "description": "API calls auth-gated", "layers_missing": ["L3", "L4"]}
  ],
  "persona_gaps": [
    {"persona": "premium-customer", "flow": "upgrade-payment", "status": "uncovered"}
  ],
  "journey_gaps": [
    {"journey": "free-to-premium-conversion", "step": 6,
     "description": "Confirmation email", "layer": "L4", "status": "uncovered"}
  ]
}
```

`implement-tests` uses this to prioritize install order — a persona gap tied to a `MUST` requirement jumps ahead of generic coverage-floor work.

---

## TESTING.md additions for this layer

Already specified in `testing-md-spec.md` under `## Traceability (observational)`. Repeated here for completeness:

```markdown
## Traceability (observational, updated by audit-tests)
rtm.total_requirements: 47
rtm.by_moscow:
  must: 22 (22 covered, 0 uncovered)
  should: 14 (11 covered, 3 uncovered)
  could: 8 (4 covered, 4 uncovered)
  wont: 3 (excluded)
rtm.orphaned_tests: 2
personas.declared: 4
personas.under_threshold: 1
journeys.declared: 6
journeys.fully_covered: 4
journeys.partial: 2
```

---

## Regulated overlay

When `tests/TESTING.md` has `Compliance overlay: HIPAA | SOX | PCI-DSS | SOC2 | GDPR | FedRAMP`:

- All `SHOULD` uncovered requirements escalate to P0 blocking.
- `COULD` uncovered escalates to P1 advisory (from P2).
- Persona coverage threshold raised to 95%.
- Journey coverage threshold raised to 95% for any journey that touches regulated data.
- Orphaned tests become P1 (not P2) — a test of something not declared in RTM is a compliance audit flag.
