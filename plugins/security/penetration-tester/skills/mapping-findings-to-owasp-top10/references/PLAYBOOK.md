# PLAYBOOK — Mapping Rules and Workflow

## Default skill → OWASP mappings (reference table)

| Cluster | Skill | OWASP | Reason |
|---|---|---|---|
| 1 | analyzing-tls-config | A02 | Cryptographic Failures |
| 1 | detecting-ssl-cert-issues | A02 | Cryptographic Failures |
| 1 | auditing-cors-policy | A01 | Broken Access Control |
| 1 | checking-http-security-headers | A05 | Security Misconfiguration |
| 1 | probing-dangerous-http-methods | A05 | Security Misconfiguration |
| 2 | detecting-exposed-secrets-files | A02 | Cryptographic Failures (.env, .git exposures) |
| 2 | detecting-debug-endpoints | A05 | Misconfiguration |
| 2 | fingerprinting-server-software | A06 | Outdated components signal |
| 2 | detecting-directory-listing | A05 | Misconfiguration |
| 3 | scanning-for-hardcoded-secrets | A02 | Hardcoded credentials |
| 3 | detecting-sql-injection-patterns | A03 | Injection |
| 3 | detecting-command-injection-patterns | A03 | Injection |
| 3 | detecting-eval-exec-usage | A03 | Injection (code execution) |
| 3 | detecting-insecure-deserialization | A08 | Integrity Failures |
| 3 | detecting-weak-cryptography | A02 | Crypto failures |
| 4 | auditing-npm-dependencies | A06 | Vulnerable Components |
| 4 | auditing-python-dependencies | A06 | Vulnerable Components |
| 4 | checking-license-compliance | A06 | Components hygiene |
| 4 | tracing-transitive-vulnerabilities | A06 | Vulnerable Components |
| 5 | confirming-pentest-authorization | A04 | Insecure Design |
| 5 | defining-pentest-scope | A04 | Insecure Design |
| 5 | recording-pentest-engagement | A09 | Logging / Monitoring |

Cluster 5 (governance) findings aren't technical application
vulnerabilities; the A04 / A09 mapping is for COVERAGE-REPORTING
purposes (so engagement-governance findings show up somewhere
in the OWASP narrative rather than being invisible).

## Overrides YAML format

```yaml
# .owasp-overrides.yaml
- skill_id: auditing-cors-policy
  owasp_category: A05:2021 — Security Misconfiguration
  reason: customer treats CORS as misconfig, not access-control

- skill_id: scanning-for-hardcoded-secrets
  detail_contains: ".env"
  owasp_category: A02:2021 — Cryptographic Failures
  reason: .env leaks treated as crypto failure for this customer

- skill_id: tracing-transitive-vulnerabilities
  detail_contains: "deep"
  owasp_category: A08:2021 — Software and Data Integrity Failures
  reason: deep-transitive vulns treated as integrity concern for this customer
```

An override applies when:

- `skill_id` matches AND
- `detail_contains` matches (if specified — substring match)

The `owasp_category` must be one of the canonical strings (e.g.
"A05:2021 — Security Misconfiguration"). The skill parses the
leading code (`A05`) for table lookup.

Add a `reason` field on every override. Reasons become part of
the engagement archive's audit trail.

## Coverage-report interpretation

### "All 10 categories covered"

Customer report's OWASP section can claim "the engagement evaluated
all 10 OWASP Top 10 categories." This is the strongest possible
coverage claim and what most customers want.

### "8 of 10 categories covered"

Customer report should explicitly note which categories had no
findings AND whether each "no findings" reflects clean results
or out-of-scope testing. Phrasing template:

> The engagement covered 8 of the 10 OWASP Top 10 (2021)
> categories. A04 (Insecure Design) and A10 (Server-Side Request
> Forgery) had no findings within this engagement's scope.

### "3 of 10 categories covered"

Either a deliberately narrow scope or a rule-table coverage gap.
Investigate before shipping the report:

1. Check the unmapped findings list. Are findings falling into the
   "no rule matched" bucket?
2. Check the scope. Did the engagement explicitly include only
   network testing (which would naturally cover A02 + A05 + A06)?
3. If the narrow coverage is intentional, document it in the
   engagement summary's scope section.

## Per-customer category-emphasis patterns

### PCI DSS customers

PCI DSS Req 6.5 lists specific vulnerability classes that must be
addressed. The skill's standard A0X mapping covers most of these.
Recommend including a "PCI DSS Req 6.5 coverage" section in the
report that cross-references A0X findings to specific Req 6.5
items. Out of scope for this skill (separate mapping).

### HIPAA customers

A02 (Crypto) and A09 (Logging) get the most scrutiny. Recommend
running A02 + A09 specifically (auditing-tls-config + checking
for security logging + monitoring failures) regardless of
broader scope.

### SOC2 customers

CC7 (System Operations) maps loosely to A06 + A09. CC8 (Change
Management) maps to A04 + A08. The full coverage report supports
the SOC2 audit narrative.

### ISO 27001 customers

Annex A.14.2 (Security in Development) maps to A04 + A08. Annex
A.12.6 (Vulnerability Management) maps to A06. The full coverage
report supports the ISO 27001 audit narrative.

## Workflow patterns

### Standalone enrichment

```bash
python3 ./scripts/map_owasp.py engagements/acme-2026-q2/
```

Enriched JSONL at `findings/all-with-owasp.jsonl`.
Coverage report at `reports/owasp-coverage.md`.

### Enrichment with overrides

```bash
python3 ./scripts/map_owasp.py engagements/acme-2026-q2/ \
    --overrides engagements/acme-2026-q2/.owasp-overrides.yaml
```

### Coverage audit only (no enrichment)

```bash
python3 ./scripts/map_owasp.py engagements/acme-2026-q2/ \
    --enrich-output /dev/null \
    --coverage-output /tmp/coverage.md
```

### Re-compose vulnerability report after enrichment

```bash
# Step 1: enrich
python3 ./scripts/map_owasp.py engagements/acme-2026-q2/

# Step 2: re-compose report from enriched findings
python3 plugins/security/penetration-tester/skills/composing-vulnerability-report/scripts/compose_report.py \
    engagements/acme-2026-q2/ \
    --source engagements/acme-2026-q2/findings/all-with-owasp.jsonl \
    --report-output engagements/acme-2026-q2/reports/vulnerability-report-v2.md
```

## When to extend the rule table

Add a new entry to `SKILL_TO_OWASP` when:

- A new cluster 1-4 skill is added to the pack.
- A skill's default classification proves consistently wrong in
  practice.
- A new CWE → OWASP mapping is needed (extend `CWE_TO_OWASP`).

Add a new entry to `DETAIL_KEYWORDS` when:

- An UNMAPPED-finding pattern is recognizable by detail keywords
  that no current rule catches.
- A detail-keyword rule is sometimes a useful fallback for
  third-party tools whose output passes through this skill.

Don't add overrides as rule-table extensions — overrides are
engagement-specific by design. Rule-table changes are global.

## Integration with executive-summary

The exec-summary skill consumes the enriched findings JSONL plus
the coverage report. The exec summary's "OWASP coverage" section
quotes per-category counts from the coverage report and risk
score from the unified findings.

Order of operations: cluster 1-4 → this skill → exec summary.
Optionally re-run compose-vulnerability-report between this skill
and exec-summary so the OWASP tags appear in the main report's
per-finding sections.
