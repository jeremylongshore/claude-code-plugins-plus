---
name: vastai-data-handling
description: |
  Manage training data and model artifacts securely on Vast.ai GPU instances.
  Use when transferring data to instances, managing checkpoints,
  or implementing secure data lifecycle on rented hardware.
  Trigger with phrases like "vastai data", "vastai upload data",
  "vastai checkpoints", "vastai data security", "vastai artifacts".
allowed-tools: Read, Write, Edit, Bash(vastai:*), Bash(ssh:*), Bash(scp:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, vast-ai, compliance, data]

---
# Vast.ai Data Handling

## Overview
Manage training data and model artifacts securely on Vast.ai GPU instances. Covers data transfer, encryption, checkpoint management, and cleanup. Critical consideration: Vast.ai instances run on shared hardware operated by third-party hosts.

## Prerequisites
- Vast.ai instance with SSH access
- Cloud storage (S3, GCS) for persistent artifacts
- Understanding of data sensitivity classification

## Instructions

### Step 1: Data Transfer Patterns

```bash
# Small datasets (<5GB): Direct SCP
scp -P $PORT -r ./data/ root@$HOST:/workspace/data/

# Large datasets (5-50GB): Compressed transfer
tar czf - ./data/ | ssh -p $PORT root@$HOST "tar xzf - -C /workspace/"

# Very large datasets (>50GB): Cloud storage staging
# Upload to S3/GCS first, then download on instance
ssh -p $PORT root@$HOST "aws s3 sync s3://bucket/dataset/ /workspace/data/"
```

### Step 2: Encrypted Data Transfer

```python
import subprocess, os

def encrypt_and_upload(local_path, host, port, remote_path, passphrase):
    """Encrypt data before transferring to Vast.ai instance."""
    encrypted = f"{local_path}.enc"
    # Encrypt with AES-256
    subprocess.run([
        "openssl", "enc", "-aes-256-cbc", "-salt", "-pbkdf2",
        "-in", local_path, "-out", encrypted,
        "-pass", f"pass:{passphrase}",
    ], check=True)

    # Transfer encrypted file
    subprocess.run([
        "scp", "-P", str(port), encrypted,
        f"root@{host}:{remote_path}.enc",
    ], check=True)

    # Decrypt on instance
    subprocess.run([
        "ssh", "-p", str(port), f"root@{host}",
        f"openssl enc -aes-256-cbc -d -pbkdf2 "
        f"-in {remote_path}.enc -out {remote_path} "
        f"-pass pass:{passphrase} && rm {remote_path}.enc"
    ], check=True)

    os.remove(encrypted)
```

### Step 3: Checkpoint to Cloud Storage

```python
import torch, boto3, os

class CloudCheckpointManager:
    def __init__(self, s3_bucket, prefix, save_every=500):
        self.s3 = boto3.client("s3")
        self.bucket = s3_bucket
        self.prefix = prefix
        self.save_every = save_every

    def save(self, model, optimizer, step, loss):
        if step % self.save_every != 0:
            return
        local_path = f"/tmp/ckpt-{step}.pt"
        torch.save({
            "step": step, "loss": loss,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
        }, local_path)
        self.s3.upload_file(local_path, self.bucket,
                           f"{self.prefix}/ckpt-{step}.pt")
        os.remove(local_path)
        print(f"Checkpoint saved: step {step}, loss {loss:.4f}")

    def load_latest(self):
        resp = self.s3.list_objects_v2(Bucket=self.bucket, Prefix=self.prefix)
        if not resp.get("Contents"):
            return None
        latest = sorted(resp["Contents"], key=lambda o: o["Key"])[-1]
        self.s3.download_file(self.bucket, latest["Key"], "/tmp/latest.pt")
        return torch.load("/tmp/latest.pt")
```

### Step 4: Secure Cleanup Before Destroy

```bash
# ALWAYS clean sensitive data before destroying an instance
ssh -p $PORT root@$HOST << 'CLEANUP'
# Remove training data and checkpoints
rm -rf /workspace/data /workspace/checkpoints /workspace/*.pt

# Clear command history
history -c && rm -f ~/.bash_history

# Overwrite sensitive files (optional, for high-security)
find /workspace -name "*.env" -exec shred -u {} \;

echo "Cleanup complete"
CLEANUP

# Then destroy
vastai destroy instance $INSTANCE_ID
```

### Step 5: Data Lifecycle Policy

| Data Type | On Instance | After Job | Retention |
|-----------|-------------|-----------|-----------|
| Training data | Decrypt on use | Delete before destroy | Source system only |
| Checkpoints | Local + cloud sync | Keep in cloud storage | 30 days |
| Final model | Local | Upload to model registry | Permanent |
| Logs | Local | Upload to logging service | 90 days |
| Temp files | /tmp | Auto-deleted on destroy | None |

## Output
- Data transfer patterns (SCP, compressed, cloud-staged)
- Encrypted transfer for sensitive datasets
- Cloud checkpoint manager with S3 integration
- Secure cleanup script before instance destruction
- Data lifecycle policy

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| SCP timeout | Large file or slow network | Use compressed transfer or cloud staging |
| Checkpoint upload fails | S3 credentials not on instance | Pass AWS creds via env vars at instance creation |
| Disk full during training | Insufficient disk allocation | Increase `--disk` or clean old checkpoints |
| Data left after destroy | Skipped cleanup | Always run cleanup script before `vastai destroy` |

## Resources
- [Vast.ai Instance Management](https://docs.vast.ai/api-reference/instances/create-instance)
- [AWS S3 CLI](https://docs.aws.amazon.com/cli/latest/reference/s3/)

## Next Steps
For enterprise access control, see `vastai-enterprise-rbac`.

## Examples

**Sensitive data workflow**: Encrypt dataset locally, SCP encrypted file to instance, decrypt on-instance, train, save checkpoints to S3, clean and destroy.

**Resume after preemption**: Load latest checkpoint from S3 on new instance, continue training from last saved step.
