---
name: performing-security-testing
version: 1.0.0
description: |
  Automate security vulnerability testing covering OWASP Top 10, SQL injection, XSS, CSRF, and authentication issues.
  Use when performing security assessments, penetration tests, or vulnerability scans.
  Trigger with phrases like "scan for vulnerabilities", "test security", or "run penetration test".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(test:security-*)
license: MIT
---

## Prerequisites

Before using this skill, ensure you have:
- Target application or API endpoint URLs accessible for testing
- Authentication credentials if testing protected resources
- Appropriate authorization to perform security testing on the target system
- Test environment configured (avoid production without explicit approval)
- Security testing tools installed (OWASP ZAP, sqlmap, or equivalent)

## Instructions

### Step 1: Define Test Scope
Identify the security testing parameters:
- Target URLs and endpoints to scan
- Authentication requirements and test credentials
- Specific vulnerability types to focus on (OWASP Top 10, injection, XSS, etc.)
- Testing depth level (passive scan vs. active exploitation)

### Step 2: Execute Security Scan
Run automated vulnerability detection:
1. Use Read tool to analyze application structure and identify entry points
2. Execute security testing tools via Bash(test:security-*) with proper scope
3. Monitor scan progress and capture all findings
4. Document identified vulnerabilities with severity ratings

### Step 3: Analyze Vulnerabilities
Process scan results to identify:
- SQL injection vulnerabilities in database queries
- Cross-Site Scripting (XSS) in user input fields
- Cross-Site Request Forgery (CSRF) token weaknesses
- Authentication and authorization bypass opportunities
- Security misconfigurations and exposed sensitive data

### Step 4: Generate Security Report
Create comprehensive documentation in {baseDir}/security-reports/:
- Executive summary with risk overview
- Detailed vulnerability findings with CVSS scores
- Proof-of-concept exploit examples where applicable
- Prioritized remediation recommendations
- Compliance assessment against security standards

## Output

The skill generates structured security assessment reports:

### Vulnerability Summary
- Total vulnerabilities discovered by severity (Critical, High, Medium, Low)
- OWASP Top 10 category mapping for each finding
- Attack surface analysis showing exposed endpoints

### Detailed Findings
Each vulnerability includes:
- Unique identifier and CVSS score
- Affected URLs, parameters, and HTTP methods
- Technical description of the security weakness
- Proof-of-concept demonstration or reproduction steps
- Potential impact on confidentiality, integrity, and availability

### Remediation Guidance
- Specific code fixes or configuration changes required
- Secure coding best practices to prevent recurrence
- Priority recommendations based on risk and effort
- Verification testing procedures after remediation

### Compliance Assessment
- Alignment with OWASP Application Security Verification Standard (ASVS)
- PCI DSS requirements if applicable to payment processing
- General Data Protection Regulation (GDPR) security considerations

## Error Handling

Common issues and solutions:

**Access Denied**
- Error: HTTP 403 or authentication failures during scan
- Solution: Verify credentials are valid and have sufficient permissions; use provided test accounts

**Rate Limiting**
- Error: Too many requests blocked by WAF or rate limiter
- Solution: Configure scan throttling to reduce request rate; use authenticated sessions to increase limits

**False Positives**
- Error: Reported vulnerabilities that cannot be exploited
- Solution: Manually verify each finding; adjust scanner sensitivity; whitelist known safe patterns

**Tool Installation Missing**
- Error: Security testing tools not found on system
- Solution: Install required tools using Bash(test:security-install) with package manager

## Resources

### Security Testing Tools
- OWASP ZAP for automated vulnerability scanning
- Burp Suite for manual penetration testing
- sqlmap for SQL injection detection and exploitation
- Nikto for web server vulnerability scanning

### Vulnerability Databases
- Common Vulnerabilities and Exposures (CVE) database
- National Vulnerability Database (NVD) for CVSS scoring
- OWASP Top 10 documentation and remediation guides

### Secure Coding Guidelines
- OWASP Secure Coding Practices checklist
- CWE (Common Weakness Enumeration) catalog
- SANS Top 25 Most Dangerous Software Errors

### Best Practices
- Always test in non-production environments first
- Obtain written authorization before security testing
- Document all testing activities for audit trails
- Validate remediation effectiveness with regression testing