---
title: "v4.15.0: Real Python Security Scanners + Products Section"
description: "Penetration testing plugin v2.0.0 with 3 production Python security scanners, Products & Services section, and sponsor page redesign."
date: "2026-02-13"
version: "4.15.0"
tags: ["release", "security", "plugins"]
---

## What's New in v4.15.0

This release brings real, production-grade security tooling to the plugin ecosystem and a new Products & Services section on the homepage.

### Penetration Testing Plugin v2.0.0

Three real Python security scanners totaling ~4,500 lines of production code:

- **security_scanner.py** — HTTP headers, SSL/TLS, endpoint probing, CORS analysis
- **dependency_auditor.py** — npm audit & pip-audit wrapper with unified reporting
- **code_security_scanner.py** — bandit + 16 regex patterns for static analysis

Plus new security reference documentation covering OWASP Top 10, Security Headers, and a Remediation Playbook.

### Products & Services Section

The homepage now features a Products & Services section with Agent37 partner integration.

### Bug Fixes

- Windows Defender false positive in penetration-tester plugin resolved (#300)
- Sponsor page pricing tiers replaced with email-for-details contact form
- stored-procedure-generator test functions renamed to avoid pytest collection conflicts
- Explore page style preservation when filtering search results

### Metrics

- 8 commits since v4.14.0
- 50+ files changed
- ~4,500 lines of new Python code (security scanners)
- 3 new reference docs (~1,100 lines)
