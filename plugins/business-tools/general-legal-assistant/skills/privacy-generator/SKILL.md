---
name: privacy-generator
description: 'Generates comprehensive privacy policies by scanning websites for data
  collection

  signals including cookies, forms, payment processors, and third-party scripts.

  Use when launching a website or app that collects user data and needs GDPR/CCPA
  compliance.

  Trigger with "/privacy-generator" or "create a privacy policy for my website".

  '
allowed-tools: Read, Write, Glob, Grep, WebFetch
version: 1.0.0
author: Intent Solutions <jeremy@intentsolutions.io>
license: MIT
tags:
- legal
- privacy-policy
- gdpr
- ccpa
- data-protection
- cookies
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Privacy Policy Generator

## Overview

Scans a website or application codebase to detect data collection signals — cookies,
web forms, payment processors, analytics scripts, social media embeds, and third-party
trackers — then generates a tailored privacy policy with 12 sections. Includes specific
GDPR rights (7 individual rights), CCPA rights (6 consumer rights), and cookie consent
banner text in both minimal and full GDPR formats.

The detection phase maps every data touchpoint to its legal basis and disclosure
requirement, ensuring the generated policy accurately reflects actual data practices
rather than relying on generic boilerplate.

> **Legal Disclaimer:** This skill generates template documents for informational and
> educational purposes only. Generated privacy policies are not a substitute for legal
> advice. Data protection requirements vary by jurisdiction, industry, and data type.
> All documents should be reviewed by a licensed attorney and/or data protection officer
> before publication. No attorney-client relationship is created by using this tool.

## Prerequisites

- A live website URL or local codebase to scan
- Knowledge of the business entity name and jurisdiction
- Understanding of what data is collected and why (the scan detects signals but cannot
  capture server-side-only processing)

## Instructions

1. **Scan for data collection signals.** Use WebFetch on the target URL to detect:

   | Signal Category | What to Look For |
   |----------------|------------------|
   | Cookies | `Set-Cookie` headers, cookie consent banners, tracking pixels |
   | Analytics | Google Analytics, Mixpanel, Amplitude, Hotjar, Segment |
   | Forms | Contact forms, registration, login, newsletter signup |
   | Payments | Stripe, PayPal, Square, Braintree, payment form fields |
   | Social | Facebook Pixel, Twitter tags, LinkedIn Insight, social login |
   | Advertising | Google Ads, Facebook Ads, retargeting pixels |
   | CDN/Third-Party | Cloudflare, AWS CloudFront, Google Fonts, embedded iframes |
   | Chat/Support | Intercom, Zendesk, Drift, live chat widgets |

2. **If scanning a codebase instead**, use Glob and Grep to find:
   - Cookie-setting code (`document.cookie`, `setCookie`, `cookies` middleware)
   - Analytics initialization (`gtag`, `analytics.track`, `mixpanel.init`)
   - Form handlers and data submission endpoints
   - Payment SDK imports and configurations
   - User model/schema definitions showing stored fields
   - Environment variables referencing third-party API keys

3. **Classify data types collected.** Map detected signals to data categories:
   - Identifiers (name, email, phone, address)
   - Financial (payment card, bank account, transaction history)
   - Technical (IP address, device info, browser fingerprint)
   - Behavioral (browsing history, click patterns, purchase history)
   - Content (user uploads, messages, reviews)
   - Sensitive (health, biometric, political — flag these for special handling)

4. **Determine legal bases (GDPR).** For each data category, assign:
   - **Consent** — marketing emails, non-essential cookies, analytics
   - **Contract** — account data, payment processing, service delivery
   - **Legitimate interest** — security logs, fraud prevention, basic analytics
   - **Legal obligation** — tax records, regulatory reporting

5. **Generate the 12-section privacy policy:**

   | # | Section | Covers |
   |---|---------|--------|
   | 1 | Introduction | Who the company is, what this policy covers |
   | 2 | Information We Collect | Data types, collection methods, sources |
   | 3 | How We Use Your Information | Purposes mapped to legal bases |
   | 4 | Cookies & Tracking | Cookie types, duration, opt-out mechanisms |
   | 5 | Information Sharing | Third parties, categories, purposes |
   | 6 | Data Retention | How long each data type is kept |
   | 7 | Your Rights Under GDPR | 7 specific rights with exercise instructions |
   | 8 | Your Rights Under CCPA | 6 specific rights with exercise instructions |
   | 9 | Data Security | Technical and organizational measures |
   | 10 | International Transfers | Cross-border data flow safeguards |
   | 11 | Children's Privacy | Age restrictions, COPPA compliance |
   | 12 | Contact & Updates | DPO contact, policy change notification |

6. **Detail GDPR rights (Section 7).** Include all seven with exercise instructions:
   1. Right of Access (Article 15) — request a copy of personal data
   2. Right to Rectification (Article 16) — correct inaccurate data
   3. Right to Erasure (Article 17) — "right to be forgotten"
   4. Right to Restrict Processing (Article 18) — limit data use
   5. Right to Data Portability (Article 20) — receive data in machine-readable format
   6. Right to Object (Article 21) — object to processing based on legitimate interest
   7. Rights Related to Automated Decision-Making (Article 22) — opt out of profiling

7. **Detail CCPA rights (Section 8).** Include all six:
   1. Right to Know — what personal information is collected
   2. Right to Delete — request deletion of personal information
   3. Right to Opt-Out — "Do Not Sell or Share My Personal Information"
   4. Right to Non-Discrimination — equal service regardless of rights exercised
   5. Right to Correct — correct inaccurate personal information
   6. Right to Limit Use of Sensitive Information — restrict sensitive data processing

8. **Generate cookie consent banner text.** Two versions:
   - **Minimal (US):** Brief notice with link to full policy
   - **Full GDPR:** Granular consent with necessary/analytics/marketing toggles

9. **Tag assumptions.** Insert `[VERIFY]` for any data practice inferred from signals
   but not confirmed by the user (e.g., `[VERIFY: Google Analytics detected — confirm
   if IP anonymization is enabled]`).

10. **Write the output file** using the naming convention below.

## Output

Generate a single Markdown file named `PRIVACY-POLICY-{company}-{YYYY-MM-DD}.md` with:

```
# Privacy Policy
**{Company Name}**

**Last Updated:** {date}
**Effective Date:** {date}

---

## Data Collection Summary
| Data Type | Source | Legal Basis | Retention |
|-----------|--------|-------------|-----------|
{table of all detected data points}

---

## 1. Introduction
{formal legal text}

> **Plain English:** {simple explanation}

{... sections 2-12 ...}

---

## Cookie Consent Banner Text

### Minimal Version (US)
{banner text}

### Full GDPR Version
{banner text with granular consent options}

---

**[VERIFY] Tags Summary:**
{numbered list of assumptions}

**Detection Results:** {count} data signals detected across {count} categories
**Generated by:** Legal Assistant Plugin — Not a substitute for legal counsel.
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Website unreachable | URL down or behind authentication | Ask for a description of data practices or codebase path |
| No data signals detected | Static site with no tracking | Generate minimal policy covering server logs and hosting |
| Sensitive data detected | Health, biometric, or financial data | Flag for enhanced protection; recommend DPO consultation |
| Multiple jurisdictions | Global audience detected | Include both GDPR and CCPA sections, add [VERIFY] for others |
| Server-side processing invisible | Cannot detect backend data flows | Ask user to describe server-side data collection |
| Third-party script unrecognized | Unknown tracking pixel or SDK | List as "unidentified third-party service" with [VERIFY] |

## Examples

**Example 1: SaaS with Analytics and Payments**

Request: "Generate a privacy policy for https://example-app.com"

Result: `PRIVACY-POLICY-ExampleApp-2026-04-02.md` detecting:
- Google Analytics 4 (behavioral data, IP address)
- Stripe payment processing (financial data)
- Intercom chat widget (identifiers, conversation content)
- HubSpot forms (email, name, company)
- 12-section policy with GDPR + CCPA rights
- Cookie consent banner in both formats
- 6 [VERIFY] tags for server-side assumptions

**Example 2: Content Blog with Newsletter**

Request: "Create privacy policy for my WordPress blog with Mailchimp newsletter"

Result: `PRIVACY-POLICY-MyBlog-2026-04-02.md` detecting:
- WordPress cookies (session, comment author)
- Mailchimp email collection (consent-based)
- Google Fonts (IP address to Google servers)
- Simplified policy focusing on minimal data collection
- GDPR consent basis for newsletter subscription

## Resources

- [ICO Privacy Notice Code of Practice](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/individual-rights/) — UK data protection authority
- [California Attorney General CCPA Guidance](https://oag.ca.gov/privacy/ccpa) — Official CCPA regulations
- [FTC Data Security Guidance](https://www.ftc.gov/business-guidance/privacy-security) — Federal data protection standards
- [GDPR Full Text (EUR-Lex)](https://eur-lex.europa.eu/eli/reg/2016/679/oj) — Official GDPR regulation
- [NIST Privacy Framework](https://www.nist.gov/privacy-framework) — US government privacy standards
- [CommonPaper DPA](https://commonpaper.com/standards/data-processing-agreement/) — CC BY 4.0 data processing terms
