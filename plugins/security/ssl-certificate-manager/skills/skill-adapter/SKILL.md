---
name: managing-ssltls-certificates
description: |
  This skill enables Claude to manage and monitor SSL/TLS certificates using the ssl-certificate-manager plugin. It is activated when the user requests actions related to SSL certificates, such as checking certificate expiry, renewing certificates, or listing installed certificates. Use this skill when the user mentions "SSL certificate", "TLS certificate", "certificate expiry", "renew certificate", or similar phrases related to SSL/TLS certificate management. The plugin can list, check, and renew certificates, providing vital information for maintaining secure connections.
---

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