---
name: checking-hipaa-compliance
description: |
  This skill enables Claude to automatically check for HIPAA (Health Insurance Portability and Accountability Act) compliance issues in codebases, infrastructure configurations, and documentation. It leverages the hipaa-compliance-checker plugin to identify potential violations related to data privacy, security, and access controls. Use this skill when the user explicitly requests to "check HIPAA compliance", "scan for HIPAA violations", "assess HIPAA readiness", or similar phrases related to HIPAA audits and security best practices. It is useful for projects handling protected health information (PHI) and requiring adherence to HIPAA regulations.
---

## Overview

This skill automates the process of identifying potential HIPAA compliance issues within a software project. By using the hipaa-compliance-checker plugin, it helps developers and security professionals proactively address vulnerabilities and ensure adherence to HIPAA guidelines.

## How It Works

1. **Analyze Request**: Claude identifies the user's intent to check for HIPAA compliance.
2. **Initiate Plugin**: Claude activates the hipaa-compliance-checker plugin.
3. **Execute Checks**: The plugin scans the specified codebase, configuration files, or documentation for potential HIPAA violations.
4. **Generate Report**: The plugin generates a detailed report outlining identified issues and their potential impact on HIPAA compliance.

## When to Use This Skill

This skill activates when you need to:
- Evaluate a codebase for HIPAA compliance before deployment.
- Identify potential HIPAA violations in existing systems.
- Assess the HIPAA readiness of infrastructure configurations.
- Verify that documentation adheres to HIPAA guidelines.

## Examples

### Example 1: Checking a codebase for HIPAA compliance

User request: "Check HIPAA compliance of the patient data API codebase."

The skill will:
1. Activate the hipaa-compliance-checker plugin.
2. Scan the specified API codebase for potential HIPAA violations.
3. Generate a report listing any identified issues, such as insecure data storage or insufficient access controls.

### Example 2: Assessing infrastructure configuration for HIPAA readiness

User request: "Assess the HIPAA readiness of our AWS infrastructure configuration."

The skill will:
1. Activate the hipaa-compliance-checker plugin.
2. Analyze the AWS infrastructure configuration files for potential HIPAA violations, such as misconfigured security groups or inadequate encryption.
3. Generate a report outlining any identified issues and recommendations for remediation.

## Best Practices

- **Specify Target**: Always clearly specify the target (e.g., codebase, configuration file, documentation) for the HIPAA compliance check.
- **Review Reports**: Carefully review the generated reports to understand the identified issues and their potential impact.
- **Prioritize Remediation**: Prioritize the remediation of identified issues based on their severity and potential impact on HIPAA compliance.

## Integration

This skill can be integrated with other security and compliance tools to provide a comprehensive view of a system's security posture. The generated reports can be used as input for vulnerability management systems and security information and event management (SIEM) platforms.