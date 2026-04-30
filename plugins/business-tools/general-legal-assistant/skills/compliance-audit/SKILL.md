---
name: compliance-audit
description: 'Performs regulatory gap analysis across 7 compliance frameworks with
  a scored

  report card and prioritized remediation roadmap. Use when assessing a website

  or application for GDPR, CCPA, ADA, PCI-DSS, CAN-SPAM, COPPA, or SOC 2 compliance.

  Trigger with "/compliance-audit" or "audit my website for regulatory compliance".

  '
allowed-tools: Read, Glob, Grep, WebFetch
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- compliance
- gdpr
- ccpa
- ada
- pci-dss
- audit
- regulatory
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Regulatory Compliance Audit

## Overview

Executes a two-phase compliance analysis — detection scan followed by framework-by-framework
evaluation — across 7 regulatory frameworks. Produces a compliance scorecard with letter
grades (A-F) per framework, identifies specific gaps, and generates a prioritized
remediation roadmap with effort estimates and timelines.

This skill reads and analyzes existing assets. It does not generate legal documents or
modify any files. The output is an audit report documenting findings and recommendations.

> **Legal Disclaimer:** This skill generates AI-assisted compliance analysis for
> informational purposes only. It does not constitute legal advice, certification, or
> attestation of compliance. Regulatory requirements are complex and jurisdiction-specific.
> All findings should be reviewed by qualified legal counsel and/or certified compliance
> professionals. No attorney-client relationship is created by using this tool.

## Prerequisites

- A live website URL or local codebase to analyze
- Access to any existing privacy policy, terms of service, or compliance documentation
- Knowledge of the business type, target audience, and geographic reach

## Instructions

### Phase 1: Detection Scan

1. **Scan the website.** Use WebFetch on the target URL to collect:
   - HTML source (meta tags, structured data, accessibility attributes)
   - Cookie and tracking behavior (Set-Cookie headers, JavaScript trackers)
   - Form elements (input types, required fields, consent checkboxes)
   - Payment indicators (payment form fields, processor scripts)
   - Third-party scripts and embeds (analytics, advertising, social)
   - SSL/TLS certificate presence
   - Content targeting indicators (age-related content, children's themes)

2. **Scan the codebase (if available).** Use Glob and Grep to find:
   - Privacy policy and terms of service files
   - Cookie consent implementation code
   - Authentication and access control patterns
   - Data encryption at rest and in transit
   - Logging and audit trail implementations
   - Age verification or gate mechanisms
   - Email sending code and unsubscribe handling
   - Payment processing integrations
   - Accessibility attributes (aria-*, alt text, semantic HTML)

3. **Build the detection inventory.** Create a structured map of findings:

   | Category | Signals Found | Frameworks Triggered |
   |----------|---------------|---------------------|
   | Data Collection | Forms, cookies, analytics | GDPR, CCPA |
   | Payments | Stripe, PayPal, card fields | PCI-DSS |
   | Accessibility | Missing alt text, no skip nav | ADA/WCAG |
   | Email Marketing | Newsletter signup, email sends | CAN-SPAM |
   | User Demographics | Age gates, child-oriented content | COPPA |
   | Security Controls | Auth, encryption, logging | SOC 2 |

### Phase 2: Framework-by-Framework Evaluation

4. **Evaluate each applicable framework.** Score against these criteria:

   **GDPR (General Data Protection Regulation)**
   - [ ] Privacy policy published and accessible
   - [ ] Legal basis documented for each processing activity
   - [ ] Cookie consent with granular opt-in (not just notice)
   - [ ] Data subject rights mechanism (access, erasure, portability)
   - [ ] Data Processing Agreement with third-party processors
   - [ ] Data breach notification procedure documented
   - [ ] Data Protection Impact Assessment for high-risk processing
   - [ ] Records of processing activities maintained
   - [ ] International transfer safeguards (SCCs, adequacy decisions)
   - [ ] DPO appointed (if required by Article 37)

   **CCPA/CPRA (California Consumer Privacy Act)**
   - [ ] "Do Not Sell or Share My Personal Information" link visible
   - [ ] Privacy policy discloses categories of personal information collected
   - [ ] Consumer request mechanism (access, delete, correct, opt-out)
   - [ ] Service provider agreements with data sharing restrictions
   - [ ] Financial incentive disclosures (if offering loyalty programs)
   - [ ] Sensitive personal information opt-out mechanism
   - [ ] Annual privacy policy update
   - [ ] Employee/applicant privacy notices (if applicable)

   **ADA/WCAG 2.1 (Accessibility)**
   - [ ] Alt text on all images
   - [ ] Keyboard navigation support
   - [ ] Color contrast ratios (4.5:1 minimum for text)
   - [ ] Form labels and error messages
   - [ ] Skip navigation links
   - [ ] ARIA landmarks and roles
   - [ ] Video captions and audio descriptions
   - [ ] Responsive design / mobile accessibility

   **PCI-DSS (Payment Card Industry)**
   - [ ] No card data stored in plaintext
   - [ ] Payment processing via certified processor (Stripe, Braintree)
   - [ ] HTTPS enforced on all payment pages
   - [ ] No card numbers in URLs, logs, or error messages
   - [ ] SAQ (Self-Assessment Questionnaire) type determined
   - [ ] Quarterly vulnerability scans (if applicable)

   **CAN-SPAM (Commercial Email)**
   - [ ] Physical mailing address in marketing emails
   - [ ] Functional unsubscribe mechanism
   - [ ] Unsubscribe honored within 10 business days
   - [ ] Accurate "From" and "Subject" headers
   - [ ] Commercial content clearly identified
   - [ ] No harvested or purchased email lists

   **COPPA (Children's Online Privacy Protection)**
   - [ ] Age screening mechanism (if content may attract children under 13)
   - [ ] Verifiable parental consent before collecting children's data
   - [ ] Direct notice to parents about data practices
   - [ ] Parental review and deletion rights
   - [ ] Data minimization for children's data
   - [ ] No behavioral advertising to children

   **SOC 2 (Trust Services Criteria)**
   - [ ] Access controls and authentication (Security)
   - [ ] System monitoring and alerting (Availability)
   - [ ] Data encryption and integrity checks (Processing Integrity)
   - [ ] Privacy policy aligned with commitments (Privacy)
   - [ ] Data handling and retention policies (Confidentiality)
   - [ ] Incident response plan documented
   - [ ] Vendor management program
   - [ ] Change management procedures

5. **Calculate compliance scores.** For each framework:
   - Count the criteria met vs. total applicable criteria
   - Calculate a percentage score
   - Assign a letter grade:

   | Grade | Score | Meaning |
   |-------|-------|---------|
   | A | 90-100% | Substantially compliant |
   | B | 75-89% | Minor gaps, low risk |
   | C | 60-74% | Moderate gaps, action needed |
   | D | 40-59% | Significant gaps, priority remediation |
   | F | 0-39% | Non-compliant, immediate action required |

6. **Generate remediation roadmap.** For each gap, provide:
   - Description of the gap
   - Regulatory risk (fine amounts, enforcement precedents)
   - Remediation action with specific steps
   - Effort estimate (hours: 1-4, 4-16, 16-40, 40+)
   - Priority tier: P0 (immediate), P1 (30 days), P2 (90 days), P3 (6 months)
   - Suggested responsible party (legal, engineering, marketing, ops)

7. **Compile the audit report** using the output format below.

## Output

Generate a single Markdown file named `COMPLIANCE-AUDIT-{company}-{YYYY-MM-DD}.md`:

```
# Regulatory Compliance Audit
**{Company Name}** — {URL or codebase path}

**Audit Date:** {date}
**Auditor:** AI Compliance Scan (Legal Assistant Plugin)
**Scope:** {frameworks evaluated}

---

## Executive Summary
{3-5 sentence overview of compliance posture, highest-risk areas, and top recommendation}

## Compliance Scorecard

| Framework | Score | Grade | Status |
|-----------|-------|-------|--------|
| GDPR | {%} | {A-F} | {Compliant / Gaps Found / Non-Compliant} |
| CCPA/CPRA | {%} | {A-F} | {status} |
| ADA/WCAG 2.1 | {%} | {A-F} | {status} |
| PCI-DSS | {%} | {A-F} | {status} |
| CAN-SPAM | {%} | {A-F} | {status} |
| COPPA | {%} | {A-F} | {status} |
| SOC 2 | {%} | {A-F} | {status} |
| **Overall** | **{%}** | **{grade}** | |

## Detection Inventory
{table of all signals detected during Phase 1}

## Detailed Findings

### GDPR
{criteria-by-criteria evaluation with PASS/FAIL/N-A}

### CCPA/CPRA
{criteria-by-criteria evaluation}

{... remaining frameworks ...}

## Remediation Roadmap

### P0 — Immediate (This Week)
| # | Gap | Framework | Action | Effort | Owner |
|---|-----|-----------|--------|--------|-------|
{high-risk items}

### P1 — Short-Term (30 Days)
{moderate-risk items}

### P2 — Medium-Term (90 Days)
{lower-risk items}

### P3 — Long-Term (6 Months)
{enhancement items}

## Risk Exposure Summary
{estimated fine exposure per framework based on published enforcement ranges}

---

**Frameworks Not Applicable:** {list with reason}
**Limitations:** AI scan cannot detect server-side controls, review organizational policies,
or assess physical security. This audit supplements but does not replace professional
compliance assessment.
**Generated by:** Legal Assistant Plugin — Not a substitute for legal counsel.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Website unreachable | URL down, behind auth, or blocked | Ask for codebase path or manual description of features |
| Framework not applicable | Business does not trigger certain regulations | Mark as N/A with explanation, exclude from overall score |
| Cannot assess server-side | No codebase access, only URL | Note limitation, recommend server-side review separately |
| Mixed signals on COPPA | Cannot determine if audience includes children | Flag for manual review, apply COPPA criteria conservatively |
| Payment processing unclear | Redirects to external checkout | Note processor, limit PCI-DSS scope to integration points |
| Existing policies not found | No privacy policy or ToS published | Score as F for policy-dependent criteria, flag as P0 |

## Examples

**Example 1: E-Commerce Website**

Request: "Audit https://example-shop.com for compliance"

Result: `COMPLIANCE-AUDIT-ExampleShop-2026-04-02.md` with:
- GDPR: C (68%) — privacy policy exists but missing granular consent, no DPA with Shopify
- CCPA: D (45%) — no "Do Not Sell" link, no consumer request mechanism
- ADA/WCAG: B (82%) — good semantic HTML, missing alt text on 12 product images
- PCI-DSS: A (95%) — Stripe checkout handles card data, HTTPS enforced
- CAN-SPAM: B (78%) — unsubscribe works, missing physical address
- COPPA: N/A — adult products only
- SOC 2: N/A — not pursuing certification
- Remediation: 14 items across P0-P2, estimated 120 hours total

**Example 2: SaaS Application Codebase**

Request: "Run a compliance audit on our codebase at ./src"

Result: `COMPLIANCE-AUDIT-SaaSApp-2026-04-02.md` with:
- GDPR: D (52%) — no data processing records, no breach notification procedure
- CCPA: C (65%) — basic privacy controls exist, missing sensitive data handling
- ADA/WCAG: F (35%) — minimal ARIA attributes, no keyboard navigation, poor contrast
- PCI-DSS: B (80%) — Stripe integration clean, but card-related strings in logs
- CAN-SPAM: A (92%) — proper unsubscribe, physical address, clear headers
- COPPA: N/A
- SOC 2: D (48%) — no incident response plan, minimal access controls
- Remediation: 23 items, accessibility overhaul as top P0

## Resources

- [ICO GDPR Guidance](https://ico.org.uk/for-organisations/guide-to-data-protection/) — UK Information Commissioner's Office
- [California Attorney General CCPA](https://oag.ca.gov/privacy/ccpa) — Official CCPA guidance and enforcement
- [FTC CAN-SPAM Compliance Guide](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business) — Federal requirements
- [W3C WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/) — Web accessibility standards
- [PCI Security Standards Council](https://www.pcisecuritystandards.org/) — Payment card security standards
- [FTC COPPA Rule](https://www.ftc.gov/legal-library/browse/rules/childrens-online-privacy-protection-rule-coppa) — Children's privacy requirements
- [AICPA SOC 2 Trust Services Criteria](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/sorhome) — SOC 2 framework
