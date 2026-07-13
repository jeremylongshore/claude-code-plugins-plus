# Guidewire CI/CD Pipeline — Implementation Guide

Extended patterns and supplementary topics for the SKILL.md.

## GitOps with Argo CD (or Flux)

Slot deployment can be expressed declaratively in git rather than imperatively from CI. The slot's desired state lives in a yaml manifest; an operator (Argo CD or Flux) reconciles the actual GCC slot state to the manifest.

```yaml
# manifests/slots/prod.yaml
apiVersion: guidewire.io/v1
kind: Slot
metadata:
  name: prod
  namespace: acme
spec:
  package: configuration-abc1234.zip
  trafficWeight: 100
  rolloutStrategy: progressive
  healthCheck:
    fnolSyntheticEvery: 5m
    failureThreshold: 3
```

Benefits: change history is git-native, audit-friendly; rollback is a git revert; multi-tenant scaling is declarative not imperative.

Cost: requires a custom controller or community-built operator that can call GCC APIs. Worth it for teams managing 5+ tenants; overkill for a single-carrier integration.

## Blue-green deploys

For changes too risky for canary (database schema migrations that cannot dual-mode, vendor library upgrades touching many call sites), blue-green:

```
Blue slot:    serves 100% of traffic, runs N
Green slot:   warm, runs N+1, no traffic
                ↓ once warm and validated
Atomic swap:  green serves 100%, blue idle
                ↓ if green is fine for 24h
Decommission: blue accepts new package as next deploy substrate
```

Requires GCC tenant to support warm-but-zero-traffic slots, which is enabled per-product on request from Guidewire Cloud Operations.

## ITIL change-management integration

Larger carriers operate under ITIL with formal change windows, CAB approval, and post-implementation reviews. CI/CD pipeline extensions for ITIL:

| ITIL element | CI/CD integration |
|---|---|
| Change request | created automatically on merge to main; PR description becomes the change description |
| CAB approval gate | required for prod promotion; integrates with ServiceNow / Jira Service Management |
| Implementation window | promotion to prod only fires within configured maintenance windows |
| Post-implementation review | 24h after promotion, automated check on SLO burn; results attached to the change record |
| Emergency change | bypass for the CAB gate with an audit trail; usable only with on-call authorization |

Integrate via webhooks; the CI tool calls the ITIL tool's API on each gate transition.

## Infrastructure-as-code for slot configuration

Slot creation, retention, traffic split, and webhook subscriptions are normally configured in GCC console — not API. As of Guidewire Cloud release `202503`, more configuration is becoming API-accessible. Where API is available, manage via Terraform:

```hcl
resource "guidewire_slot" "prod_canary" {
  name              = "prod-canary"
  product           = "PolicyCenter"
  parent_slot       = guidewire_slot.prod.id
  traffic_weight    = 5
  decommission_after_days = 30
}
```

Terraform-backed slot config is preferable when slots are short-lived (created per release for canary, destroyed after retirement); manual creation works fine for stable long-lived slots.

## Self-hosted CI runners

Some carriers prohibit running CI on shared cloud infrastructure (data residency, FedRAMP). Self-hosted runners on GitHub Actions, GitLab CI's runner-on-prem, or Jenkins agents inside the carrier's network are all viable. Considerations:

- Runner image must include JDK 17, gradle, sops, age, AWS CLI (or equivalent) for artifact upload
- Network egress to GCC API endpoints required; egress to public package repos may be restricted, requiring a private mirror
- Secrets in CI runner environment must follow the same SOPS+age discipline as production runtime; do not paste plaintext into CI vault

## Deployment freezes

Standard practice for the insurance industry: freeze deploys during specific windows when policy/claim activity surges and incident response is constrained.

Common freezes:

- **Year-end (Dec 20 – Jan 5)** — renewal volume peaks
- **Hurricane season landfalls** — for catastrophe carriers, the active CAT period
- **Annual policy effective date concentrations** — for crop insurance lines, around planting/harvest dates
- **Carrier-specific** — quarterly close, annual statement preparation

CI gate enforces:

```yaml
- name: Check deploy freeze
  run: |
    if [ "$(date -u +%Y-%m-%d)" \> "2026-12-20" ] && [ "$(date -u +%Y-%m-%d)" \< "2027-01-06" ]; then
      echo "::error::Year-end deploy freeze in effect (Dec 20 – Jan 5)"; exit 1
    fi
```

Override via documented break-glass process with on-call leadership approval.

## Per-PR preview environments

For UI-heavy changes, a per-PR preview slot speeds up reviewer feedback. Each PR creates a short-lived slot, deploys the PR's package, and posts the URL to the PR. Closes when the PR merges or after 7 days.

Cost: GCC tenants typically charge per slot; budget per-PR previews against the tenant's slot quota.

## Continuous compliance

Each promotion to prod can emit a compliance event consumed by the carrier's GRC platform:

```json
{
  "event": "deployment.completed",
  "tenant": "acme",
  "slot": "prod",
  "package": "configuration-abc1234.zip",
  "git_sha": "abc1234",
  "approver": "user@carrier.com",
  "approval_record": "https://tickets/CHG-12345",
  "tests_passed": ["compileGosu", "GUnit", "check", "uat-regression"],
  "deployed_at": "2026-04-15T14:00:00Z"
}
```

Auditors querying "show me every prod change in Q1" get a clean list with approval evidence and test results — much faster than reconstructing from CI logs.

## Related

- `SKILL.md` — production patterns
- `references/API_REFERENCE.md` — GCC slot APIs, gradle tasks, CI workflow templates
- Sibling `guidewire-local-dev-loop` — local feedback loop these gates extend
- Sibling `guidewire-migration-and-upgrade` — version-upgrade workflow
