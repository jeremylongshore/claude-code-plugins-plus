---
name: performing-security-audits
description: |
  This skill allows Claude to conduct comprehensive security audits of code, infrastructure, and configurations. It leverages various tools within the security-pro-pack plugin, including vulnerability scanning, compliance checking, cryptography review, and infrastructure security analysis. Use this skill when a user requests a "security audit," "vulnerability assessment," "compliance review," or any task involving identifying and mitigating security risks. It helps to ensure code and systems adhere to security best practices and compliance standards.
---

## Overview

This skill empowers Claude to perform in-depth security audits across various domains, from code vulnerability scanning to compliance verification and infrastructure security assessment. It utilizes the specialized tools within the security-pro-pack to provide a comprehensive security posture analysis.

## How It Works

1. **Analysis Selection**: Claude determines the appropriate security-pro-pack tool (e.g., `Security Auditor Expert`, `Compliance Checker`, `Crypto Audit`) based on the user's request and the context of the code or system being analyzed.
2. **Execution**: Claude executes the selected tool, providing it with the relevant code, configuration files, or API endpoints.
3. **Reporting**: Claude aggregates and presents the findings in a clear, actionable report, highlighting vulnerabilities, compliance issues, and potential security risks, along with suggested remediation steps.

## When to Use This Skill

This skill activates when you need to:
- Assess the security of code for vulnerabilities like those in the OWASP Top 10.
- Evaluate compliance with standards such as HIPAA, PCI DSS, GDPR, or SOC 2.
- Review cryptographic implementations for weaknesses.
- Perform container security scans or API security audits.

## Examples

### Example 1: Vulnerability Assessment

User request: "Please perform a security audit on this authentication code to find any potential vulnerabilities."

The skill will:
1. Invoke the `Security Auditor Expert` agent.
2. Analyze the provided authentication code for common vulnerabilities.
3. Generate a report detailing any identified vulnerabilities, their severity, and recommended fixes.

### Example 2: Compliance Check

User request: "Check this application against GDPR compliance requirements."

The skill will:
1. Invoke the `Compliance Checker` agent.
2. Evaluate the application's architecture and code against GDPR guidelines.
3. Generate a report highlighting any non-compliant areas and suggesting necessary changes.

## Best Practices

- **Specificity**: Provide clear and specific instructions about the scope of the audit (e.g., "audit this specific function" instead of "audit the whole codebase").
- **Context**: Include relevant context about the application, infrastructure, or data being audited to enable more accurate and relevant results.
- **Iteration**: Use the skill iteratively, addressing the most critical findings first and then progressively improving the overall security posture.

## Integration

This skill seamlessly integrates with all other components of the security-pro-pack plugin. It also works well with Claude's existing code analysis capabilities, allowing for a holistic and integrated security review process.