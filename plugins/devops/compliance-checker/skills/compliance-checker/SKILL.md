---
name: checking-infrastructure-compliance
description: |
  This skill allows Claude to check infrastructure compliance against industry standards such as SOC2, HIPAA, and PCI-DSS. It analyzes existing infrastructure configurations and reports on potential compliance violations. Use this skill when the user asks to assess compliance, identify security risks related to compliance, or generate reports on compliance status for SOC2, HIPAA, or PCI-DSS. Trigger terms include: "compliance check", "SOC2 compliance", "HIPAA compliance", "PCI-DSS compliance", "compliance report", "infrastructure compliance", "security audit", "assess compliance".
allowed-tools: Read, Write, Edit, Grep, Glob, Bash
version: 1.0.0
---

## Overview

This skill enables Claude to evaluate infrastructure configurations against common compliance frameworks. It helps identify potential vulnerabilities and gaps in compliance, providing valuable insights for remediation.

## How It Works

1. **Receiving Request**: Claude receives a user request to check infrastructure compliance.
2. **Analyzing Configuration**: Claude analyzes the infrastructure configuration based on the requested compliance standard (SOC2, HIPAA, PCI-DSS).
3. **Generating Report**: Claude generates a report highlighting potential compliance violations and areas for improvement.

## When to Use This Skill

This skill activates when you need to:
- Assess infrastructure compliance against SOC2, HIPAA, or PCI-DSS standards.
- Identify potential security risks related to compliance violations.
- Generate reports on the compliance status of your infrastructure.

## Examples

### Example 1: Assessing SOC2 Compliance

User request: "Run a SOC2 compliance check on our AWS infrastructure."

The skill will:
1. Analyze the AWS infrastructure configuration against SOC2 requirements.
2. Generate a report identifying any non-compliant configurations and recommended remediations.

### Example 2: Identifying HIPAA Compliance Issues

User request: "Check our cloud environment for HIPAA compliance violations."

The skill will:
1. Analyze the cloud environment's security settings and configurations against HIPAA regulations.
2. Provide a report outlining potential HIPAA violations and suggested corrective actions.

## Best Practices

- **Specify Standard**: Always specify the compliance standard (SOC2, HIPAA, PCI-DSS) you want to check against.
- **Provide Context**: Provide as much context as possible about your infrastructure to ensure accurate analysis.
- **Review Results**: Carefully review the generated report and implement the recommended remediations.

## Integration

This skill can be integrated with other DevOps tools and plugins to automate compliance checks and integrate compliance into the development lifecycle. For example, it can be used in conjunction with infrastructure-as-code tools to ensure compliance from the start.