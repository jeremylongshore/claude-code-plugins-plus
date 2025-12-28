---
name: analyzing-security-headers
description: |
  Analyze HTTP security headers of web domains to identify vulnerabilities and misconfigurations.
  Use when you need to audit website security headers, assess header compliance, or get security recommendations for web applications.
  Trigger with phrases like "analyze security headers", "check HTTP headers", "audit website security headers", or "evaluate CSP and HSTS configuration".
  
allowed-tools: Read, WebFetch, WebSearch, Grep
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Security Headers Analyzer

This skill provides automated assistance for security headers analyzer tasks.

## Overview

Analyzes HTTP response headers (HSTS, CSP, etc.) for a target domain, scores gaps, and recommends concrete remediations.

## Prerequisites

Before using this skill, ensure:
- Target URL or domain name is accessible
- Network connectivity for HTTP requests
- Permission to scan the target domain
- Optional: Save results to {baseDir}/security-reports/

## Instructions

1. Collect the target URL/domain and environment context (CDN/proxy, redirects).
2. Fetch response headers (HTTP/HTTPS) and capture redirects/cookies.
3. Compare headers to recommended baselines and score gaps.
4. Provide concrete remediation steps and verify fixes.

### 1. Domain Input Phase

Accept domain specification:
- Full URL with protocol (https://example.com)
- Domain name only (example.com - will test HTTPS first)
- Multiple domains for batch analysis
- Specific paths for header variation testing

### 2. Header Fetching Phase

Retrieve HTTP response headers:
- Make HEAD or GET request to target
- Capture all security-relevant headers
- Test both HTTP and HTTPS responses
- Record redirect chains and final destination

### 3. Analysis Phase

Evaluate each security header against best practices:

**Critical Headers**:
- Strict-Transport-Security (HSTS)
- Content-Security-Policy (CSP)
- X-Frame-Options
- X-Content-Type-Options
- Permissions-Policy

**Important Headers**:
- Referrer-Policy
- Cross-Origin-Embedder-Policy (COEP)
- Cross-Origin-Opener-Policy (COOP)
- Cross-Origin-Resource-Policy (CORP)

**Additional Checks**:
- Server header information disclosure
- X-Powered-By header exposure
- Cookie security attributes (Secure, HttpOnly, SameSite)

### 4. Grading Phase

Calculate security score:
- A+ (95-100): All critical headers properly configured
- A (85-94): Critical headers present, minor issues
- B (75-84): Most headers present, some weaknesses
- C (65-74): Missing critical headers
- D (50-64): Significant security gaps
- F (<50): Multiple critical vulnerabilities

### 5. Report Generation Phase

Create comprehensive report with:
- Overall security grade and numeric score
- Missing headers with impact assessment
- Misconfigured headers with specific issues
- Remediation recommendations with examples
- Priority ranking for fixes

## Output

The skill produces:

**Primary Output**: Security headers analysis report

**Report Structure**:
```
# Security Headers Analysis - example.com


## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.
## Overall Grade: B (82/100)

## Critical Headers Status
✅ Strict-Transport-Security: Present (max-age=31536000; includeSubDomains)
❌ Content-Security-Policy: Missing
✅ X-Frame-Options: Present (DENY)
✅ X-Content-Type-Options: Present (nosniff)
⚠️  Permissions-Policy: Misconfigured

## Detailed Findings

### Missing Headers (High Priority)
1. Content-Security-Policy
   - Risk: XSS vulnerability exposure
   - Recommendation: Implement strict CSP
   - Example: Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'

### Misconfigured Headers
1. Permissions-Policy
   - Current: geolocation=*
   - Issue: Allows all origins
   - Fix: geolocation=(self)

## Priority Actions
1. Add Content-Security-Policy (Critical)
2. Fix Permissions-Policy wildcard (High)
3. Add Referrer-Policy (Medium)
```

**Optional Outputs**:
- JSON format for automation: {baseDir}/security-reports/headers-DOMAIN-YYYYMMDD.json
- CSV for spreadsheet analysis
- Comparison report for multiple domains

## Error Handling

**Common Issues and Resolutions**:

1. **Domain Unreachable**
   - Error: "Failed to connect to example.com"
   - Resolution: Check domain spelling, network connectivity, firewall rules
   - Fallback: Test alternate protocols (HTTP vs HTTPS)

2. **SSL/TLS Errors**
   - Error: "SSL certificate verification failed"
   - Resolution: Note in report, test with certificate validation disabled
   - Impact: Indicates HSTS not properly enforced

3. **Redirect Loops**
   - Error: "Too many redirects"
   - Resolution: Report redirect chain, analyze headers at each hop
   - Note: Headers may differ across redirect chain

4. **Rate Limiting**
   - Error: "HTTP 429 Too Many Requests"
   - Resolution: Implement exponential backoff, reduce request frequency
   - Fallback: Queue domain for later analysis

5. **Mixed Content Issues**
   - Error: "Headers differ between HTTP and HTTPS"
   - Resolution: Report both sets, highlight critical differences
   - Recommendation: Ensure HSTS enforces HTTPS-only

## Examples

- "Analyze security headers for https://claudecodeplugins.io and explain any CSP/HSTS issues."
- "Check headers for example.com and provide a remediation checklist."

## Resources

**Security Header References**:
- OWASP Secure Headers Project: https://owasp.org/www-project-secure-headers/
- MDN Security Headers Guide: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers#security
- Security Headers Scanner: https://securityheaders.com/

**Header-Specific Documentation**:
- CSP Reference: https://content-security-policy.com/
- HSTS Preload: https://hstspreload.org/
- Permissions Policy: https://www.w3.org/TR/permissions-policy/

**Best Practice Guides**:
- NIST Web Security Guidelines: https://pages.nist.gov/800-63-3/
- Mozilla Observatory: https://observatory.mozilla.org/

**Testing Tools**:
- Online header checker: https://securityheaders.com/
- Browser DevTools Network tab for manual inspection
- curl command for command-line testing: `curl -I https://example.com`

**Integration Examples**:
- Automated header checks in CI/CD pipelines
- Periodic scanning with alerting on grade degradation
- Compliance reporting for security audits
