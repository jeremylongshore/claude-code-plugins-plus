---
name: generating-security-audit-reports
description: |
  Generate comprehensive security audit reports for applications and systems.
  Use when you need to assess security posture, identify vulnerabilities, evaluate compliance status, or create formal security documentation.
  Trigger with phrases like "create security audit report", "generate security assessment", "audit security posture", or "PCI-DSS compliance report".
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash(security-scan:*), report-gen:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

## Prerequisites

Before using this skill, ensure:
- Security scan data or logs are available in {baseDir}/security/
- Access to application configuration files
- Security tool outputs (e.g., vulnerability scanners, SAST/DAST results)
- Compliance framework documentation (if applicable)
- Write permissions for generating report files

## Instructions

### 1. Data Collection Phase

Gather security information from available sources:
- Read vulnerability scan results
- Analyze security configurations
- Review access control policies
- Check encryption implementations
- Examine authentication mechanisms

### 2. Analysis Phase

Process collected data to identify:
- Critical vulnerabilities (CVSS scores, exploitability)
- Security misconfigurations
- Compliance gaps against standards (PCI-DSS, GDPR, HIPAA, SOC 2)
- Access control weaknesses
- Data protection issues

### 3. Report Generation Phase

Create structured audit report with:
- Executive summary with risk overview
- Detailed vulnerability findings with severity ratings
- Compliance status matrix
- Risk assessment and prioritization
- Remediation recommendations with timelines
- Technical appendices with evidence

### 4. Output Formatting

Generate report in requested format:
- Markdown for version control
- HTML for stakeholder review
- JSON for integration with ticketing systems
- PDF-ready structure for formal documentation

## Output

The skill produces:

**Primary Output**: Comprehensive security audit report saved to {baseDir}/reports/security-audit-YYYYMMDD.md

**Report Structure**:
```
# Security Audit Report - [System Name]
## Executive Summary
- Overall risk rating
- Critical findings count
- Compliance status

## Vulnerability Findings
### Critical (CVSS 9.0+)
- [CVE-XXXX-XXXX] Description
- Impact assessment
- Remediation steps

### High (CVSS 7.0-8.9)
[Similar structure]

## Compliance Assessment
- PCI-DSS: 85% compliant (gaps identified)
- GDPR: 92% compliant
- SOC 2: In progress

## Remediation Plan
Priority matrix with timelines

## Technical Appendices
Evidence and scan outputs
```

**Secondary Outputs**:
- Vulnerability tracking JSON for issue systems
- Executive summary slide deck outline
- Remediation tracking checklist

## Error Handling

**Common Issues and Resolutions**:

1. **Missing Scan Data**
   - Error: "No security scan results found"
   - Resolution: Specify alternate data sources or run preliminary scans
   - Fallback: Generate report from configuration analysis only

2. **Incomplete Compliance Framework**
   - Error: "Cannot assess [STANDARD] compliance - requirements unavailable"
   - Resolution: Request framework checklist or use general best practices
   - Fallback: Note limitation in report with partial assessment

3. **Access Denied to Configuration Files**
   - Error: "Permission denied reading {baseDir}/config/"
   - Resolution: Request elevated permissions or provide configuration exports
   - Fallback: Generate report with available data, note gaps

4. **Large Dataset Processing**
   - Error: "Scan results exceed processing capacity"
   - Resolution: Process in batches by severity or component
   - Fallback: Focus on critical/high findings first

## Resources

**Security Standards References**:
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE Top 25: https://cwe.mitre.org/top25/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework

**Compliance Frameworks**:
- PCI-DSS Requirements: https://www.pcisecuritystandards.org/
- GDPR Compliance Checklist: https://gdpr.eu/checklist/
- HIPAA Security Rule: https://www.hhs.gov/hipaa/for-professionals/security/

**Vulnerability Databases**:
- National Vulnerability Database: https://nvd.nist.gov/
- CVE Details: https://www.cvedetails.com/

**Report Templates**:
- Use {baseDir}/templates/security-audit-template.md if available
- Default structure follows NIST SP 800-115 guidelines

**Integration Points**:
- Export findings to JIRA/GitHub Issues for tracking
- Generate compliance evidence for SOC 2 audits
- Link to SIEM/logging systems for evidence validation