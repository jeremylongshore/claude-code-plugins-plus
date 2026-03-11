---
name: vastai-data-handling
description: |
  Implement Vast.ai PII handling, data retention, and GDPR/CCPA compliance patterns.
  Use when handling sensitive data, implementing data redaction, configuring retention policies,
  or ensuring compliance with privacy regulations for Vast.ai integrations.
  Trigger with phrases like "vastai data", "vastai PII",
  "vastai GDPR", "vastai data retention", "vastai privacy", "vastai CCPA".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vast.ai Data Handling

## Overview
Manage training data and model artifacts securely on Vast.ai GPU instances. Covers secure data transfer to instances, training data encryption, model checkpoint management, and instance cleanup to prevent data leakage.

## Prerequisites
- Vast.ai account with SSH access
- Understanding of GPU instance lifecycle
- Encryption tools (gpg, openssl)
- rsync for data transfer

## Instructions

### Step 1: Encrypted Data Transfer
```bash
#!/bin/bash
# scripts/secure-upload.sh
# Encrypt data before sending to Vast.ai instance

INSTANCE_IP=$1
INSTANCE_PORT=$2
DATA_DIR=$3
ENCRYPTION_KEY=${ENCRYPTION_KEY:-""}

if [ -z "$ENCRYPTION_KEY" ]; then
  echo "ERROR: Set ENCRYPTION_KEY environment variable"
  exit 1
fi

# Compress and encrypt
tar czf - "$DATA_DIR" | \
  openssl enc -aes-256-cbc -salt -pbkdf2 -pass env:ENCRYPTION_KEY \
  > /tmp/data.tar.gz.enc

# Transfer encrypted archive
rsync -avz --progress \
  -e "ssh -p $INSTANCE_PORT -o StrictHostKeyChecking=no" \
  /tmp/data.tar.gz.enc "root@${INSTANCE_IP}:/workspace/"

# Decrypt on instance
ssh -p "$INSTANCE_PORT" "root@${INSTANCE_IP}" << 'REMOTE'
  cd /workspace
  openssl enc -d -aes-256-cbc -pbkdf2 -pass env:ENCRYPTION_KEY \
    -in data.tar.gz.enc | tar xzf -
  rm data.tar.gz.enc
REMOTE

rm /tmp/data.tar.gz.enc
echo "Secure upload complete"
```

### Step 2: Training Data Validation
```python
import json
from pathlib import Path

def validate_training_data(data_dir: str) -> dict:
    """Validate training data before uploading to Vast.ai."""
    issues = []
    stats = {"files": 0, "total_size_mb": 0}

    for path in Path(data_dir).rglob("*"):
        if path.is_file():
            stats["files"] += 1
            stats["total_size_mb"] += path.stat().st_size / 1_048_576

            # Check for accidentally included secrets
            if path.name in [".env", "credentials.json", "secrets.yaml"]:
                issues.append(f"SECRET FILE: {path}")

            # Check for PII in JSONL training files
            if path.suffix == ".jsonl":
                with open(path) as f:
                    for i, line in enumerate(f):
                        record = json.loads(line)
                        text = json.dumps(record)
                        if check_pii(text):
                            issues.append(f"PII in {path}:{i+1}")

    return {"stats": stats, "issues": issues, "safe": len(issues) == 0}

def check_pii(text: str) -> bool:
    """Basic PII detection."""
    import re
    patterns = [
        r'\b[\w.+-]+@[\w-]+\.[\w.]+\b',  # Email
        r'\b\d{3}-\d{2}-\d{4}\b',          # SSN
        r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
    ]
    return any(re.search(p, text) for p in patterns)
```

### Step 3: Model Checkpoint Management
```python
import subprocess
import json
from datetime import datetime

def download_checkpoints(
    instance_id: int,
    remote_dir: str = "/workspace/checkpoints",
    local_dir: str = "./checkpoints"
):
    """Download model checkpoints from Vast.ai instance."""
    info = get_instance_info(instance_id)

    Path(local_dir).mkdir(parents=True, exist_ok=True)

    subprocess.run([
        "rsync", "-avz", "--progress",
        "--include=*.pt", "--include=*.safetensors",
        "--include=*.json", "--exclude=*",
        "-e", f"ssh -p {info['ssh_port']}",
        f"root@{info['ssh_host']}:{remote_dir}/",
        f"{local_dir}/"
    ], check=True)

    # Create manifest
    manifest = {
        "downloaded_at": datetime.utcnow().isoformat(),
        "instance_id": instance_id,
        "files": [str(p) for p in Path(local_dir).glob("*")],
    }

    with open(f"{local_dir}/manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    return manifest
```

### Step 4: Secure Instance Cleanup
```python
def secure_destroy_instance(instance_id: int):
    """Securely wipe data before destroying instance."""
    info = get_instance_info(instance_id)

    # Wipe sensitive directories on instance
    try:
        subprocess.run([
            "ssh", "-p", str(info["ssh_port"]),
            f"root@{info['ssh_host']}",
            "rm -rf /workspace/data /workspace/checkpoints /workspace/*.env && "
            "echo 'Data wiped'"
        ], timeout=30, check=True)
    except Exception as e:
        print(f"Warning: cleanup failed ({e}), destroying anyway")

    # Destroy the instance
    subprocess.run(
        ["vastai", "destroy", "instance", str(instance_id)],
        check=True
    )
    print(f"Instance {instance_id} destroyed")
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Secrets in training data | Unvalidated dataset | Run `validate_training_data` before upload |
| Data left on instance | Instance destroyed without cleanup | Use `secure_destroy_instance` |
| Transfer interrupted | Network issue | Use rsync (resumes partial transfers) |
| Unencrypted transfer | Forgot encryption step | Always use `secure-upload.sh` script |

## Examples

### Full Secure Training Pipeline
```python
# 1. Validate data
result = validate_training_data("./training-data")
assert result["safe"], f"Data issues: {result['issues']}"

# 2. Upload encrypted
os.system(f"./scripts/secure-upload.sh {ip} {port} ./training-data")

# 3. Train on instance...

# 4. Download results and cleanup
download_checkpoints(instance_id)
secure_destroy_instance(instance_id)
```

## Resources
- [Vast.ai Security](https://vast.ai/docs/security)
- [Vast.ai CLI](https://vast.ai/docs/cli/commands)
