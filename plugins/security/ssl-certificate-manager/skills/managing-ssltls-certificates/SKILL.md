---
name: managing-ssltls-certificates
description: |
  This skill enables AI assistant to manage and monitor ssl/tls certificates using the ssl-certificate-manager plugin. it is activated when the user requests actions related to ssl certificates, such as checking certificate expiry, renewing certificates, ... Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Bash(cmd:*), Grep, Glob
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Ssl Certificate Manager

This skill provides automated assistance for ssl certificate manager tasks.

## Overview

This skill empowers Claude to seamlessly interact with the ssl-certificate-manager plugin, facilitating efficient management and monitoring of SSL/TLS certificates. It allows for quick checks of certificate expiry dates, automated renewal processes, and comprehensive listings of installed certificates.

## How It Works

1. **Identify Intent**: Claude analyzes the user's request for keywords related to SSL/TLS certificate management.
2. **Plugin Activation**: The ssl-certificate-manager plugin is automatically activated.
3. **Command Execution**: Based on the user's request, Claude executes the appropriate command within the plugin (e.g., checking expiry, renewing certificate, listing certificates).
4. **Result Presentation**: Claude presents the results of the command execution to the user in a clear and concise format.

## When to Use This Skill

This skill activates when you need to:
- Check the expiry date of an SSL/TLS certificate.
- Renew an SSL/TLS certificate.
- List all installed SSL/TLS certificates.
- Investigate SSL/TLS certificate issues.

## Examples

### Example 1: Checking Certificate Expiry

User request: "Check the expiry date of my SSL certificate for example.com"

The skill will:
1. Activate the ssl-certificate-manager plugin.
2. Execute the command to check the expiry date for the specified domain.
3. Display the expiry date to the user.

### Example 2: Renewing a Certificate

User request: "Renew my SSL certificate for api.example.org"

The skill will:
1. Activate the ssl-certificate-manager plugin.
2. Execute the command to renew the SSL certificate for the specified domain.
3. Confirm the renewal process to the user.

## Best Practices

- **Specificity**: Provide the full domain name when requesting certificate checks or renewals.
- **Context**: If encountering errors, provide the full error message to Claude for better troubleshooting.
- **Verification**: After renewal, always verify the new certificate is correctly installed and functioning.

## Integration

This skill can be used in conjunction with other security-related plugins to provide a comprehensive security overview. For example, it can be integrated with vulnerability scanning tools to identify potential weaknesses related to outdated or misconfigured certificates.

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