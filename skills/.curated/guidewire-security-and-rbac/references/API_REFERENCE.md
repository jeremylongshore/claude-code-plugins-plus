# Guidewire Security & RBAC — Reference

GCC role catalog, scope strings, audit endpoints, and compliance mapping that informed the patterns in `SKILL.md`.

## GCC role-to-scope mapping (illustrative)

Carrier configurations vary; treat the table below as a starting taxonomy. Confirm exact scope strings under **GCC > Identity & Access > Applications > [your-app] > Permissions**.

| Role | Scope strings | Use case |
|---|---|---|
| `pc.account.read` | `pc.account.read` | reporting, lookup, broker portal account search |
| `pc.account.write` | `pc.account.read pc.account.write` | broker portal account create/update |
| `pc.policy.read` | `pc.policy.read` | renewal job, billing integration, claims policy lookup |
| `pc.policy.write` | `pc.policy.read pc.policy.write` | renewal-on-bind, endorsement automation |
| `pc.submission.write` | `pc.account.read pc.policy.read pc.submission.write` | broker quote-and-bind |
| `cc.claim.read` | `cc.claim.read` | claims dashboards, customer self-service |
| `cc.claim.write` | `cc.claim.read cc.claim.write` | FNOL intake, claim updates |
| `cc.reserve.write` | `cc.claim.read cc.reserve.write` | reserve-setting jobs |
| `cc.payment.write` | `cc.claim.read cc.payment.write` | payment authorization at the integration's tier |
| `bc.invoice.read` | `bc.invoice.read` | billing reconciliation |

Read roles are cumulative — `pc.policy.write` does not imply `pc.policy.read`; assign both. Reverse is true: `pc.policy.read` is a prerequisite of writes that depend on the resource being readable.

## Audit endpoints (Guidewire-side)

GCC exposes a tenant audit log accessible via the GCC console, not over Cloud API. Cross-reference internal `integration_audit` rows against the GCC audit log when investigating incidents — the GCC log shows what the API received; the internal table shows why the integration sent it.

## Compliance frameworks the skill addresses

| Framework | Control | How this skill addresses it |
|---|---|---|
| SOC 2 CC6.1 | Logical and Physical Access Controls | least-privilege roles, per-tenant Service Applications, scope-drift detection |
| SOC 2 CC6.6 | Encryption of Data at Rest | SOPS+age encryption of secrets in repo |
| SOC 2 CC7.2 | System Monitoring | `integration_audit` table + observability skill alerts |
| OWASP A01:2021 | Broken Access Control | scope hardening, scope-drift gate, per-tenant credentials |
| OWASP A02:2021 | Cryptographic Failures | SOPS+age, anchored sed for dotenv eval, no committed plaintext |
| OWASP A09:2021 | Security Logging Failures | redactPII at logger transport, audit table |
| NAIC Model Audit Rule | data security and incident response | detect-and-rotate runbook, audit-trail retention |
| HIPAA (where applicable) | safeguards for PHI | redactPII includes PHI fields when WC/medical lines are in scope |

## PII field reference

The Cloud API resources most likely to carry regulated PII:

| Resource | Path | PII type |
|---|---|---|
| `Contact` | `attributes.taxId` | SSN/EIN — direct identifier |
| `Contact` | `attributes.dateOfBirth` | DOB — direct identifier |
| `Contact` | `attributes.driversLicenseNumber` | DL — direct identifier |
| `Contact` | `attributes.primaryPhone.phoneNumber` | phone — quasi-identifier |
| `Contact` | `attributes.primaryEmail` | email — quasi-identifier |
| `Contact` | `attributes.primaryAddress.*` | address — quasi-identifier |
| `Claim` | `attributes.description` | claim narrative — may include medical/legal detail |
| `Claim` | `attributes.officialID` | claim official id — sensitive in cross-tenant scenarios |
| `Activity` | `attributes.subject` and `notes` | adjuster narrative — frequently contains PHI/PII |
| `Document` | document content | varies — treat all unstructured documents as PII |

The redactor should default-deny — fields not on an allowlist redact; fields on the allowlist pass through. Allowlist creep is a slower failure than redactor creep.

## Per-tenant credential file layout

```
secrets/
├── secrets.dev.sops.yaml           # all tenants share dev (low-risk)
├── secrets.uat.tenant-a.sops.yaml  # per-tenant UAT
├── secrets.uat.tenant-b.sops.yaml
├── secrets.prod.tenant-a.sops.yaml # per-tenant prod
├── secrets.prod.tenant-b.sops.yaml
└── .sops.yaml                      # creation_rules with per-file recipient maps
```

The runtime resolves which file to decrypt based on the tenant routing layer; never load all tenants' secrets into one process if you can avoid it.

## Detect-and-rotate runbook (concrete steps)

1. **Suspicion** — credential observed in any non-secret-store location (Slack, log, public commit, screenshot, support ticket)
2. **Rotate in GCC** — issue a new `client_secret`; set the old one as the secondary if the runtime supports dual-secret window
3. **Update encrypted file** — `sops secrets.<env>.<tenant>.sops.yaml`, set new value, commit, push
4. **Deploy** — trigger the deployment that re-reads the file; confirm runtime is using the new value (token claims include `iat` — verify recent issuance)
5. **Audit window** — pull GCC access logs for the integration's `client_id` over the leak window; flag any calls outside expected pattern (off-hours, unexpected IP, unusual scope)
6. **Document** — incident row in audit table with `reason: "credential-rotation-suspected-leak"`; brief postmortem if the leak duration was non-trivial

Target rotation time: <30 minutes from suspicion to deploy. Practiced quarterly.

## Related references

- `references/implementation-guide.md` — extended walkthrough including Vault Agent and dynamic secrets
- Sibling `guidewire-install-auth/references/API_REFERENCE.md` — auth-side patterns this hardens
- Sibling `guidewire-observability-and-incident-response` — alerting on the signals this skill produces
