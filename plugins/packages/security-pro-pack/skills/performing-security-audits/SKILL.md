---
name: performing-security-audits
description: |
  Analyze code, infrastructure, and configurations by conducting comprehensive security audits. It leverages tools within the security-pro-pack plugin, including vulnerability scanning, compliance checking, and cryptography review. Use when assessing security or running audits. Trigger with phrases like 'security scan', 'audit', or 'vulnerability'.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Security Pro Pack

This skill provides automated assistance for security pro pack tasks.

## Overview


This skill provides automated assistance for security pro pack tasks.
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

## Prerequisites

- Appropriate file access permissions
- Required dependencies installed

## Instructions

1. Invoke this skill when the trigger conditions are met
2. Provide necessary context and parameters
3. Review the generated output
4. Apply modifications as needed

## Output

The skill produces structured output relevant to the task.

## Error Handling

- Invalid input: Prompts for correction
- Missing dependencies: Lists required components
- Permission errors: Suggests remediation steps

## Resources

- Project documentation
- Related skills and commands
