---
name: encrypting-and-decrypting-data
description: Validate encryption implementations and cryptographic practices. Use when reviewing data security measures. Trigger with 'check encryption', 'validate crypto', or 'review security keys'.
version: 1.0.0
allowed-tools: "Read, Write, Edit, Grep, Glob, Bash(security:*), Bash(scan:*), Bash(audit:*)"
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---
# Encryption Tool

This skill provides automated assistance for encryption tool tasks.

## Overview

This skill empowers Claude to handle data encryption and decryption tasks seamlessly. It leverages the encryption-tool plugin to provide a secure way to protect sensitive information, ensuring confidentiality and integrity.

## How It Works

1. **Identify Encryption/Decryption Request**: Claude analyzes the user's request to determine whether encryption or decryption is required.
2. **Select Encryption Method**: Claude prompts the user to specify the desired encryption algorithm (e.g., AES, RSA). If not specified, a default secure method is chosen.
3. **Execute Encryption/Decryption**: Claude utilizes the encryption-tool plugin to perform the encryption or decryption operation on the provided data or file.
4. **Return Encrypted/Decrypted Data**: Claude presents the encrypted or decrypted data to the user, or saves the result to a file as requested.

## When to Use This Skill

This skill activates when you need to:
- Encrypt sensitive data before storage or transmission.
- Decrypt previously encrypted data for access or processing.
- Generate encrypted files for secure archiving.

## Examples

### Example 1: Encrypting a Text File

User request: "Encrypt the file 'sensitive_data.txt' using AES."

The skill will:
1. Activate the encryption-tool plugin.
2. Encrypt the contents of 'sensitive_data.txt' using AES encryption.
3. Save the encrypted data to a new file (e.g., 'sensitive_data.txt.enc').

### Example 2: Decrypting an Encrypted File

User request: "Decrypt the file 'confidential.txt.enc'."

The skill will:
1. Activate the encryption-tool plugin.
2. Decrypt the contents of 'confidential.txt.enc' using the appropriate decryption key (assumed to be available or prompted for).
3. Save the decrypted data to a new file (e.g., 'confidential.txt').

## Best Practices

- **Key Management**: Always store encryption keys securely and avoid hardcoding them in scripts.
- **Algorithm Selection**: Choose encryption algorithms based on the sensitivity of the data and the required security level. Consider industry best practices and compliance requirements.
- **Data Integrity**: Implement mechanisms to verify the integrity of encrypted data to detect tampering or corruption.

## Integration

This skill can be integrated with other Claude Code plugins, such as file management tools, to automate the encryption and decryption of files during data processing workflows. It can also be combined with security auditing tools to ensure compliance with security policies.

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
