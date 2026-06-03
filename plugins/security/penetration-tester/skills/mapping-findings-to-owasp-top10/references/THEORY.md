# THEORY — OWASP Top 10 Mapping

## What the OWASP Top 10 actually is

The OWASP Top 10 is a community-curated list of the most critical
web application security risks, updated every 3-4 years. The
current version is the 2021 edition. The Top 10 is NOT a complete
taxonomy of all possible vulnerabilities — it's a prioritization
framework. Findings outside the Top 10 still matter; they just
don't get their own A0X slot.

The 2021 edition's categories (with their derivation from 2017
predecessors):

| 2021 | Notes |
|---|---|
| A01 Broken Access Control | Promoted from A05 (2017); broadest category, includes path traversal + IDOR |
| A02 Cryptographic Failures | Renamed from A03 "Sensitive Data Exposure"; emphasizes the failure modes not the data |
| A03 Injection | Demoted from A01 (2017); XSS folded in here |
| A04 Insecure Design | NEW; threat-modeling-failure findings |
| A05 Security Misconfiguration | Includes XML External Entities (was A04 in 2017) |
| A06 Vulnerable and Outdated Components | Promoted from A09 (2017) |
| A07 Identification and Authentication Failures | Renamed from A02 "Broken Authentication" |
| A08 Software and Data Integrity Failures | NEW; supply-chain-attack-shaped |
| A09 Security Logging and Monitoring Failures | Renamed from A10 (2017) |
| A10 Server-Side Request Forgery | NEW as a Top 10 entry |

The 2025 edition is in draft as of this skill's authorship. When
it ships, this skill's mapping table should be reviewed against
the new category set.

## CWE → OWASP cross-walk

OWASP publishes an authoritative mapping from CWE identifiers to
OWASP categories at https://owasp.org/Top10/A0X_2021-<name>/. The
mapping is one-to-many in both directions: a single CWE can map
to multiple OWASP categories depending on context, and a single
OWASP category encompasses many CWEs.

This skill's `CWE_TO_OWASP` table captures the most common
mappings deterministically. Edge cases:

- CWE-200 (Information Exposure) — typically A01 but can map to
  A05 or A09 depending on context.
- CWE-352 (CSRF) — included in A01 in 2021 (was A08 in 2017).
- CWE-89 (SQL Injection) — A03, no ambiguity.

When a CWE has multiple plausible mappings, the skill picks the
most common one in practice. Override via the engagement-specific
overrides YAML for cases where the customer expects a different
classification.

## Why deterministic rules, not LLM classification

It's tempting to feed each finding to an LLM and ask "which OWASP
category fits best?" Two problems:

1. **Reproducibility.** A pentest report claims to be the result
   of a defined methodology. An LLM-classified report changes
   slightly on every regeneration (model temperature, prompt
   variation, training-data drift). Auditors hate this.

2. **Explainability.** A finding's mapping needs a defensible
   reason ("this is A06 because the source skill is
   `auditing-npm-dependencies` which detects vulnerable
   third-party components" is defensible; "the LLM said so" is
   not).

The skill uses a deterministic rule table. Rules are auditable.
The classifier can be wrong, but it's wrong consistently — and
the operator can extend the table to fix patterns.

## Rule precedence

The skill applies rules in this order:

1. **Engagement-specific overrides** (from `--overrides FILE`).
   Highest precedence; lets customers express their own
   classification preferences.
2. **CWE-based mapping** when the finding has a `cwe_id`.
3. **Skill-ID default** when no CWE is present or matches.
4. **Detail-keyword fallback** as a last-resort heuristic.

Each successful classification records WHICH rule matched in the
operational Finding. Operators can see the reasoning chain when
debugging unexpected classifications.

## Coverage interpretation

The coverage report shows count per A0X category. Interpretation:

| Pattern | What it usually means |
|---|---|
| All 10 categories have findings | Broad-coverage engagement, comprehensive scope |
| 6-9 categories | Typical engagement; some categories not in scope |
| 1-5 categories | Narrow scope OR rule table missed mappings |
| 0 categories with HIGH/CRITICAL | Either remarkably clean target OR scans didn't run |

The skill flags fewer-than-5 categories as MEDIUM. The operator
should determine whether the narrow coverage is intentional (and
document so) or a sign of incomplete testing.

## When a finding genuinely doesn't fit a single category

Some findings are cross-cutting:

- A misconfigured database cluster (A05 Misconfiguration + A09
  Logging + A02 Crypto-at-rest) — could legitimately appear in
  three categories.
- A supply-chain compromise (A06 Components + A08 Software Integrity)
  — both apply.
- An authentication bypass via path traversal (A07 + A01).

The Top 10 doesn't tolerate multi-category findings. The convention
is to pick the PRIMARY category (the failure mode that most
directly causes exploitation) and accept that the finding will be
reported under one A0X bucket. Cross-references in the report body
can point to the secondary category.

## Customer-specific category preferences

Some customers care about specific A0X categories for compliance
reasons:

- **PCI DSS** customers care about A02 (Crypto) and A07 (Auth).
- **Healthcare (HIPAA)** customers care about A02 + A09 (Logging).
- **SOC2 CC7** customers want broad coverage across all categories.

The skill's overrides YAML is the mechanism for capturing these
preferences. An override re-classifies a finding's category for
the specific engagement without changing the default rule table.

## OWASP Top 10 vs ASVS

The OWASP Application Security Verification Standard (ASVS) is a
much more granular framework — 286 verification requirements across
14 chapters. Some engagements demand ASVS coverage instead of (or
in addition to) Top 10 coverage. This skill maps Top 10 only;
ASVS mapping would be a separate skill (or extension to this one)
because the rule table is differently shaped.

## Mapping precision tradeoffs

The skill optimizes for:

- **Coverage** — every finding gets a mapping if at all possible.
- **Reproducibility** — same input → same output, always.
- **Auditability** — the rule that matched is recorded.
- **Extensibility** — operators can add overrides without code changes.

It does NOT optimize for:

- **Per-finding precision** — a finding might fit two categories;
  the skill picks one deterministically.
- **2025-edition forward compatibility** — when OWASP 2025
  finalizes, the table needs review.
- **ASVS coverage** — out of scope.

These tradeoffs are deliberate. The skill is a triage tool, not a
substitute for human judgment on contested classifications.
