---
name: Assisting with SOC2 Audit Preparation
description: |
  This skill assists with SOC2 audit preparation by automating tasks related to evidence gathering and documentation. It leverages the soc2-audit-helper plugin to generate reports, identify potential compliance gaps, and suggest remediation steps. Use this skill when the user requests help with "SOC2 audit", "compliance check", "security controls", "audit preparation", or "evidence gathering" related to SOC2. It streamlines the initial stages of SOC2 compliance, focusing on automated data collection and preliminary analysis.
---

## Overview

This skill empowers Claude to assist users in preparing for a SOC2 audit. It automates the process of gathering evidence, analyzing security controls, and identifying potential compliance gaps, significantly reducing the manual effort involved in SOC2 preparation.

## How It Works

1. **Analyze Request**: Claude identifies the user's intent to prepare for a SOC2 audit.
2. **Gather Evidence**: The `soc2-audit-helper` plugin is invoked to collect relevant data and artifacts from the user's environment based on common SOC2 requirements.
3. **Generate Report**: The plugin generates a comprehensive report summarizing the current state of compliance, highlighting potential areas of concern.

## When to Use This Skill

This skill activates when you need to:
- Prepare for a SOC2 audit.
- Assess current security controls against SOC2 requirements.
- Gather evidence for SOC2 compliance.

## Examples

### Example 1: Generating a SOC2 Readiness Report

User request: "Generate a SOC2 readiness report for my AWS environment."

The skill will:
1. Invoke the `soc2-audit-helper` plugin.
2. Generate a report detailing the compliance status of the AWS environment based on SOC2 criteria.

### Example 2: Identifying Compliance Gaps

User request: "What are the compliance gaps in my current security posture related to SOC2?"

The skill will:
1. Invoke the `soc2-audit-helper` plugin.
2. Analyze the current security configuration and identify areas where it falls short of SOC2 requirements.

## Best Practices

- **Specificity**: Provide as much detail as possible about the environment and specific SOC2 requirements.
- **Regular Updates**: Run the audit helper regularly to track progress and identify new compliance gaps.
- **Review Findings**: Carefully review the generated reports and address any identified issues promptly.

## Integration

This skill can be integrated with other security and compliance tools to provide a more comprehensive view of the organization's security posture. For example, it can be used in conjunction with vulnerability scanners and configuration management tools to identify and remediate security weaknesses.