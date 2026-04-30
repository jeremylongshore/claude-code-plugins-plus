---
name: terms-generator
description: 'Generates comprehensive terms of service by analyzing a website or application

  to detect business type, data collection, and user interactions. Use when launching

  a website, app, or SaaS product that needs terms of service with GDPR/CCPA compliance.

  Trigger with "/terms-generator" or "create terms of service for my website".

  '
allowed-tools: Read, Write, Glob, Grep, WebFetch
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- terms-of-service
- compliance
- gdpr
- ccpa
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Terms of Service Generator

## Overview

Scans a website or application to understand the business model, user interactions,
data collection practices, and third-party integrations, then generates a comprehensive
terms of service document with 16 sections. Includes GDPR and CCPA compliance provisions,
plain English summaries after each section, and `[VERIFY]` tags for assumptions that
require human confirmation.

The generated ToS adapts its language and provisions based on the detected business type
(e-commerce, SaaS, marketplace, content platform, mobile app, etc.).

> **Legal Disclaimer:** This skill generates template documents for informational and
> educational purposes only. Generated terms of service are not a substitute for legal
> advice. All documents should be reviewed by a licensed attorney before publication.
> Regulatory requirements vary by jurisdiction and business type. No attorney-client
> relationship is created by using this tool.

## Prerequisites

- A live website URL or local codebase to analyze
- Knowledge of the business entity name and jurisdiction
- Understanding of whether the service involves payments, user accounts, or user-generated content

## Instructions

1. **Analyze the website or application.** Use WebFetch to scan the target URL. Identify:
   - Business type (SaaS, e-commerce, marketplace, content, API, mobile app)
   - User interaction patterns (accounts, purchases, subscriptions, content uploads)
   - Data collection mechanisms (forms, cookies, analytics scripts, payment processors)
   - Third-party integrations (Stripe, Google Analytics, social login, CDNs)
   - Geographic indicators (language, currency, server location)

2. **If a codebase is available instead**, use Glob and Read to scan for:
   - Cookie/tracking implementations
   - Authentication flows
   - Payment integrations
   - User data models
   - API endpoints that accept user input

3. **Gather business details from the user:**
   - Legal entity name and type (LLC, Corp, sole proprietor)
   - Business address and jurisdiction
   - Contact email for legal notices
   - Minimum user age requirement
   - Whether the service is free, paid, or freemium

4. **Determine applicable compliance frameworks:**
   - **GDPR** — if serving EU/EEA users (detected via language, .eu domain, Euro pricing)
   - **CCPA/CPRA** — if serving California users or meeting revenue/data thresholds
   - **COPPA** — if the service could attract users under 13
   - **ADA/WCAG** — if a US-based public-facing service
   - **PCI-DSS** — if processing payment card data
   - **CAN-SPAM** — if sending marketing emails

5. **Generate the 16-section Terms of Service:**

   | # | Section | Covers |
   |---|---------|--------|
   | 1 | Agreement to Terms | Acceptance mechanism, effective date |
   | 2 | Description of Service | What the service provides |
   | 3 | User Accounts | Registration, security, age requirements |
   | 4 | Acceptable Use Policy | Prohibited conduct, content standards |
   | 5 | User-Generated Content | Ownership, licenses, moderation rights |
   | 6 | Intellectual Property | Company IP rights, trademarks, DMCA |
   | 7 | Payment Terms | Pricing, billing cycles, refunds (if applicable) |
   | 8 | Free Trials & Subscriptions | Trial terms, auto-renewal, cancellation |
   | 9 | Privacy & Data Collection | Reference to privacy policy, GDPR/CCPA summary |
   | 10 | Third-Party Services | Links, integrations, disclaimers |
   | 11 | Disclaimers & Warranties | "As-is" provision, warranty limitations |
   | 12 | Limitation of Liability | Liability caps, excluded damages |
   | 13 | Indemnification | User indemnification obligations |
   | 14 | Termination | Grounds, notice, effect of termination |
   | 15 | Governing Law & Disputes | Jurisdiction, arbitration, class action waiver |
   | 16 | General Provisions | Modifications, severability, entire agreement, contact |

6. **Add plain English summaries.** After each section, include a blockquote:
   `> **In Plain English:** {simple summary of what this means for users}`

7. **Insert compliance-specific provisions:**
   - GDPR: Data processing legal basis, right to erasure, DPO contact, data portability
   - CCPA: "Do Not Sell My Personal Information" rights, opt-out mechanism
   - COPPA: Age verification, parental consent mechanism

8. **Tag all assumptions.** Place `[VERIFY]` before any clause based on inferred information:
   - `[VERIFY: assumed SaaS model based on subscription pricing detected]`
   - `[VERIFY: jurisdiction set to Delaware — confirm with business owner]`
   - `[VERIFY: assumed no users under 13 — confirm age policy]`

9. **Write the output file** using the naming convention below.

## Output

Generate a single Markdown file named `TERMS-OF-SERVICE-{company}-{YYYY-MM-DD}.md` with:

```
# Terms of Service
**{Company Name}**

**Last Updated:** {date}
**Effective Date:** {date}

---

## Table of Contents
1. [Agreement to Terms](#1-agreement-to-terms)
{... all 16 sections ...}

---

## 1. Agreement to Terms
{formal legal text}

> **In Plain English:** {simple explanation}

## 2. Description of Service
{formal legal text}

> **In Plain English:** {simple explanation}

{... sections 3-16 ...}

---

## Contact Information
{business contact details}

---
**[VERIFY] Tags Summary:**
{numbered list of all assumptions needing confirmation}

**Compliance Frameworks Applied:** {GDPR, CCPA, etc.}
**Generated by:** Legal Assistant Plugin — Not a substitute for legal counsel.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Website unreachable | URL is down or behind auth | Ask user for a description of the service or local codebase path |
| Cannot determine business type | Minimal website content | Ask user directly about their business model |
| Payment detection ambiguous | Cannot tell if free or paid | Ask user to confirm pricing model |
| International complexity | Multiple jurisdictions detected | Generate provisions for all detected jurisdictions, add [VERIFY] |
| Dynamic content not scannable | SPA with client-side rendering | Ask user to describe features or provide sitemap |
| Missing company details | User did not provide entity info | Use [VERIFY] placeholders, list in summary |

## Examples

**Example 1: SaaS Application**

Request: "Create terms of service for https://example-saas.com — we're a project management tool"

Result: `TERMS-OF-SERVICE-ExampleSaaS-2026-04-02.md` with:
- 16 sections with SaaS-specific provisions
- Payment terms for subscription model (detected via Stripe integration)
- GDPR provisions (EU users detected via multi-language support)
- CCPA provisions (US-based company)
- User-generated content section for project data
- 8 [VERIFY] tags for assumptions

**Example 2: E-Commerce Store**

Request: "Generate ToS for my Shopify store selling handmade jewelry"

Result: `TERMS-OF-SERVICE-HandmadeJewels-2026-04-02.md` with:
- E-commerce focused provisions (returns, shipping, product descriptions)
- Payment terms referencing Shopify Payments / PayPal
- No user-generated content section (simplified)
- Consumer protection provisions per FTC guidelines
- CCPA opt-out mechanism

## Resources

- [FTC Business Guidance on Terms](https://www.ftc.gov/business-guidance) — Federal Trade Commission compliance
- [California Attorney General CCPA](https://oag.ca.gov/privacy/ccpa) — CCPA regulations and guidance
- [ICO Guide to Data Protection](https://ico.org.uk/for-organisations/) — UK/GDPR compliance guidance
- [CommonPaper Standard Terms](https://commonpaper.com/standards/) — CC BY 4.0 open-source terms
- [Termly ToS Generator](https://termly.io/) — Reference for section structures
- [SBA Small Business Legal Resources](https://www.sba.gov/) — US government business guidance
