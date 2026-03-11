---
name: apollo-security-basics
description: |
  Apply Apollo.io API security best practices.
  Use when securing Apollo integrations, managing API keys,
  or implementing secure data handling.
  Trigger with phrases like "apollo security", "secure apollo api",
  "apollo api key security", "apollo data protection".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Apollo Security Basics

## Overview
Implement security best practices for Apollo.io API integrations including key management, data protection, and access controls.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-security-basics:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-security-basics/references/implementation-guide.md)`

## Output
- Secure API key management
- PII redaction for logging
- Data retention controls
- Role-based access patterns
- Security audit checklist

## Error Handling
| Issue | Mitigation |
|-------|------------|
| Key exposure | Immediate rotation |
| PII in logs | Implement redaction |
| Unauthorized access | Audit and revoke |
| Data breach | Follow incident response |

## Resources
- [Apollo Security Practices](https://www.apollo.io/security)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [GDPR for API Developers](https://gdpr.eu/)

## Next Steps
Proceed to `apollo-prod-checklist` for production deployment.
