---
name: validating-cors-policies
description: Validate CORS policies for security issues and misconfigurations. Use when reviewing cross-origin resource sharing. Trigger with 'validate CORS', 'check CORS policy', or 'review cross-origin'.
version: 1.0.0
allowed-tools: "Read, WebFetch, WebSearch, Grep"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Cors Policy Validator

This skill provides automated assistance for cors policy validator tasks.

## Overview

This skill empowers Claude to assess the security and correctness of CORS policies. By leveraging the cors-policy-validator plugin, it identifies misconfigurations and potential vulnerabilities in CORS settings, helping developers build more secure web applications.

## How It Works

1. **Analyze CORS Configuration**: The skill receives the CORS configuration details, such as headers or policy files.
2. **Validate Policy**: It utilizes the cors-policy-validator plugin to analyze the provided configuration against established security best practices.
3. **Report Findings**: The skill presents a detailed report outlining any identified vulnerabilities or misconfigurations in the CORS policy.

## When to Use This Skill

This skill activates when you need to:
- Validate a CORS policy for a web application.
- Check the CORS configuration of an API endpoint.
- Identify potential security vulnerabilities in existing CORS implementations.

## Examples

### Example 1: Validating a CORS Policy File

User request: "Validate the CORS policy in `cors_policy.json`"

The skill will:
1. Read the `cors_policy.json` file.
2. Use the cors-policy-validator plugin to analyze the CORS configuration.
3. Output a report detailing any identified vulnerabilities or misconfigurations.

### Example 2: Checking CORS Headers for an API Endpoint

User request: "Check CORS headers for the API endpoint at `https://example.com/api`"

The skill will:
1. Fetch the CORS headers from the specified API endpoint.
2. Use the cors-policy-validator plugin to analyze the headers.
3. Output a report summarizing the CORS configuration and any potential issues.

## Best Practices

- **Configuration Source**: Always specify the source of the CORS configuration (e.g., file path, URL) for accurate validation.
- **Regular Validation**: Regularly validate CORS policies, especially after making changes to the application or API.
- **Heuristic Analysis**: Consider supplementing validation with manual review and heuristic analysis to catch subtle vulnerabilities.

## Integration

This skill can be integrated with other security-related plugins to provide a more comprehensive security assessment. For example, it can be used in conjunction with vulnerability scanning tools to identify potential cross-site scripting (XSS) vulnerabilities related to CORS misconfigurations.

## Prerequisites

- Access to codebase and configuration files in {baseDir}/
- Security scanning tools installed as needed
- Understanding of security standards and best practices
- Permissions for security analysis operations

## Instructions

1. Identify security scan scope and targets
2. Configure scanning parameters and thresholds
3. Execute security analysis systematically
4. Analyze findings for vulnerabilities and compliance gaps
5. Prioritize issues by severity and impact
6. Generate detailed security report with remediation steps

## Output

- Security scan results with vulnerability details
- Compliance status reports by standard
- Prioritized list of security issues by severity
- Remediation recommendations with code examples
- Executive summary for stakeholders

## Error Handling

If security scanning fails:
- Verify tool installation and configuration
- Check file and directory permissions
- Validate scan target paths
- Review tool-specific error messages
- Ensure network access for dependency checks

## Resources

- Security standard documentation (OWASP, CWE, CVE)
- Compliance framework guidelines (GDPR, HIPAA, PCI-DSS)
- Security scanning tool documentation
- Vulnerability remediation best practices
