---
name: detecting-infrastructure-drift
description: |
  This skill enables Claude to detect infrastructure drift from a desired state. It uses the `drift-detect` command to identify discrepancies between the current infrastructure configuration and the intended configuration, as defined in infrastructure-as-code tools like Terraform. Use this skill when the user asks to check for infrastructure drift, identify configuration changes, or ensure that the current infrastructure matches the desired state. It is particularly useful in DevOps workflows for maintaining infrastructure consistency and preventing configuration errors. Trigger this skill when the user mentions "drift detection," "infrastructure changes," "configuration drift," or requests a "drift report."
---

## Overview

This skill empowers Claude to identify and report on deviations between the current state of your infrastructure and its defined desired state. By leveraging the `drift-detect` command, it provides insights into configuration inconsistencies, helping maintain infrastructure integrity and prevent unexpected issues.

## How It Works

1. **Invocation**: The user requests drift detection.
2. **Drift Analysis**: Claude executes the `drift-detect` command.
3. **Report Generation**: The command analyzes the infrastructure and identifies any deviations from the defined configuration.
4. **Result Presentation**: Claude presents a report detailing the detected drift, including affected resources and configuration differences.

## When to Use This Skill

This skill activates when you need to:
- Identify infrastructure drift in your environment.
- Ensure that your infrastructure configuration matches the desired state.
- Generate a report detailing discrepancies between the current and desired infrastructure configurations.

## Examples

### Example 1: Checking for Infrastructure Drift

User request: "Check for infrastructure drift in my production environment."

The skill will:
1. Execute the `drift-detect` command.
2. Present a report detailing any detected drift, including resource changes and configuration differences.

### Example 2: Identifying Configuration Changes

User request: "Are there any configuration changes that haven't been applied to my infrastructure?"

The skill will:
1. Execute the `drift-detect` command.
2. Provide a summary of configuration changes that are present in the desired state but not reflected in the current infrastructure.

## Best Practices

- **Regular Monitoring**: Schedule regular drift detection checks to proactively identify and address configuration inconsistencies.
- **Version Control**: Ensure your infrastructure-as-code configurations are version-controlled to track changes and facilitate rollbacks.
- **Automated Remediation**: Implement automated remediation workflows to automatically correct detected drift and maintain infrastructure consistency.

## Integration

This skill can be integrated with other DevOps tools and plugins to automate infrastructure management workflows. For example, it can be used in conjunction with configuration management tools like Ansible or Puppet to automatically remediate detected drift. It also complements infrastructure-as-code tools like Terraform by providing a mechanism for verifying that the deployed infrastructure matches the defined configuration.