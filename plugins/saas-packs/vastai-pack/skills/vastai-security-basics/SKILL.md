---
name: vastai-security-basics
description: |
  Apply Vast.ai security best practices for API keys and instance access.
  Use when securing API keys, hardening SSH access to GPU instances,
  or auditing Vast.ai security configuration.
  Trigger with phrases like "vastai security", "vastai secrets",
  "secure vastai", "vastai API key security", "vastai ssh security".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, api, security]

---
# Vast.ai Security Basics

## Overview
Security best practices for Vast.ai API keys, SSH access to GPU instances, data protection on rented hardware, and credential management. Vast.ai instances run as root on shared hardware, requiring careful attention to data lifecycle.

## Prerequisites
- Vast.ai account with API key
- Understanding of SSH key management
- Secrets manager available (optional but recommended)

## Instructions

### Step 1: API Key Management

```bash
# Never commit API keys to git
echo '.vast_api_key' >> .gitignore
echo '.env' >> .gitignore

# Use environment variables, not files in repos
export VASTAI_API_KEY="$(vault kv get -field=api_key secret/vastai)"

# Rotate keys periodically at cloud.vast.ai > Account > API Keys
```

```python
# Fail fast on missing credentials
import os

def get_api_key():
    key = os.environ.get("VASTAI_API_KEY")
    if not key:
        key_file = os.path.expanduser("~/.vast_api_key")
        if os.path.exists(key_file):
            key = open(key_file).read().strip()
    if not key:
        raise ValueError("VASTAI_API_KEY not set and ~/.vast_api_key not found")
    return key
```

### Step 2: SSH Key Security

```bash
# Generate a dedicated key pair for Vast.ai instances
ssh-keygen -t ed25519 -f ~/.ssh/vastai_key -C "vastai-instances" -N ""

# Upload public key at cloud.vast.ai > Account > SSH Keys

# Use the dedicated key for connections
ssh -i ~/.ssh/vastai_key -p PORT root@HOST
```

### Step 3: Data Protection on Shared Hardware

```python
def secure_cleanup(instance_id, ssh_host, ssh_port):
    """Securely wipe data before destroying an instance."""
    import subprocess
    # Overwrite sensitive files before instance destruction
    subprocess.run([
        "ssh", "-p", str(ssh_port), "-o", "StrictHostKeyChecking=no",
        f"root@{ssh_host}",
        "rm -rf /workspace/data /workspace/checkpoints /root/.ssh/authorized_keys; "
        "history -c"
    ], check=True)
    # Then destroy
    subprocess.run(["vastai", "destroy", "instance", str(instance_id)], check=True)
```

### Step 4: Network Security

- Use SSH tunnels for any services exposed on instances
- Never expose ports with sensitive data to the public internet
- Transfer data over SCP/SFTP, not unencrypted HTTP
- Encrypt training data before upload; decrypt on-instance

### Step 5: Credential Rotation Checklist

- [ ] API key rotated every 90 days
- [ ] SSH keys dedicated to Vast.ai (not shared with production)
- [ ] Old SSH keys removed from cloud.vast.ai after rotation
- [ ] `.vast_api_key` file permissions set to `600`
- [ ] No API keys in shell history (`export` from a sourced file, not typed)

## Output
- API key loaded from environment or secrets manager
- Dedicated SSH key pair for Vast.ai instances
- Secure cleanup before instance destruction
- Network security guidelines
- Credential rotation checklist

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| API key leaked in git | Committed `.env` or key file | Rotate key immediately; add to `.gitignore` |
| SSH key rejected | Wrong key or not uploaded | Verify key is at cloud.vast.ai > SSH Keys |
| Data left on destroyed instance | Forgot to clean up | Use `secure_cleanup()` before destroy |
| Key file world-readable | Wrong permissions | `chmod 600 ~/.vast_api_key ~/.ssh/vastai_key` |

## Resources
- [Vast.ai CLI Security](https://docs.vast.ai/cli/get-started)
- [SSH Key Management](https://docs.vast.ai/api-reference/introduction)

## Next Steps
For production deployment checklist, see `vastai-prod-checklist`.

## Examples

**Vault integration**: Load API key from HashiCorp Vault at runtime, never write to disk, and use SSH agent forwarding for key management.

**Ephemeral instances**: Treat every Vast.ai instance as throwaway. Never store persistent state on instances; always upload data, process, download results, and destroy.
