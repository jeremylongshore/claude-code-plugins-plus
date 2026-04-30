---
name: oraclecloud-local-dev-loop
description: 'Set up a productive local OCI development workflow using CLI and SDK
  instead of the web console.

  Use when the OCI Console is too slow, setting up CLI profiles, or building shell
  aliases for common operations.

  Trigger with "oci local dev", "oci cli setup", "oraclecloud dev workflow", "avoid
  oci console".

  '
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(oci:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Local Dev Loop

## Overview

The OCI web console is slow, hard to navigate, and requires dozens of clicks for common operations. A local dev workflow using the OCI CLI and Python SDK replaces the console for everything: listing resources, launching instances, managing object storage, and checking service health. Profile switching lets you target dev/staging/prod from the same terminal.

**Purpose:** Set up a complete local OCI development environment with CLI profiles, shell aliases, environment variable management, and common workflow scripts that eliminate the need for the web console.

## Prerequisites

- **Completed `oraclecloud-install-auth`** — valid `~/.oci/config` with at least one profile
- **Python 3.8+** with `pip install oci oci-cli`
- **Bash or Zsh** shell
- OCIDs for your compartments (Governance > Compartments in the Console — last time you need it)

## Instructions

### Step 1: Install and Verify the OCI CLI

```bash
pip install oci-cli

# Verify installation
oci --version

# Quick connectivity test
oci iam region list --output table
```

### Step 2: Set Up Multiple Profiles

Edit `~/.oci/config` with profiles for each environment:

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaa_YOUR_USER
fingerprint=ab:cd:ef:12:34:56:78:90:ab:cd:ef:12:34:56:78:90
tenancy=ocid1.tenancy.oc1..aaaa_PROD_TENANCY
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem

[dev]
user=ocid1.user.oc1..aaaa_YOUR_USER
fingerprint=ab:cd:ef:12:34:56:78:90:ab:cd:ef:12:34:56:78:90
tenancy=ocid1.tenancy.oc1..aaaa_DEV_TENANCY
region=us-phoenix-1
key_file=~/.oci/oci_api_key_dev.pem

[staging]
user=ocid1.user.oc1..aaaa_YOUR_USER
fingerprint=12:34:56:78:90:ab:cd:ef:12:34:56:78:90:ab:cd:ef
tenancy=ocid1.tenancy.oc1..aaaa_STAGING_TENANCY
region=eu-frankfurt-1
key_file=~/.oci/oci_api_key_staging.pem
```

Switch profiles with the `--profile` flag or `OCI_CLI_PROFILE` env var:

```bash
# CLI flag
oci compute instance list --compartment-id <OCID> --profile dev

# Environment variable (applies to all commands in session)
export OCI_CLI_PROFILE=dev
oci compute instance list --compartment-id <OCID>
```

### Step 3: Environment Variables and .env File

Create a project `.env` file for compartment OCIDs and region defaults:

```bash
# .env — OCI project configuration (NEVER commit this file)
OCI_COMPARTMENT_ID="ocid1.compartment.oc1..aaaa_YOUR_COMPARTMENT"
OCI_TENANCY_ID="ocid1.tenancy.oc1..aaaa_YOUR_TENANCY"
OCI_REGION="us-ashburn-1"
OCI_CLI_PROFILE="DEFAULT"
```

```bash
# Add to .gitignore
echo ".env" >> .gitignore

# Source in your shell
source .env
```

### Step 4: Shell Aliases for Common Operations

Add these to your `~/.bashrc` or `~/.zshrc`:

```bash
# --- OCI Shell Aliases ---

# Profile switching
alias oci-dev='export OCI_CLI_PROFILE=dev && echo "Switched to dev"'
alias oci-staging='export OCI_CLI_PROFILE=staging && echo "Switched to staging"'
alias oci-prod='export OCI_CLI_PROFILE=DEFAULT && echo "Switched to prod"'

# Compute
alias oci-instances='oci compute instance list --compartment-id $OCI_COMPARTMENT_ID --output table --query "data[*].{Name:\"display-name\",State:\"lifecycle-state\",Shape:shape,OCID:id}"'
alias oci-running='oci compute instance list --compartment-id $OCI_COMPARTMENT_ID --lifecycle-state RUNNING --output table'

# Object Storage
alias oci-buckets='oci os bucket list --compartment-id $OCI_COMPARTMENT_ID --output table --query "data[*].{Name:name,Created:\"time-created\"}"'

# Networking
alias oci-vcns='oci network vcn list --compartment-id $OCI_COMPARTMENT_ID --output table'
alias oci-subnets='oci network subnet list --compartment-id $OCI_COMPARTMENT_ID --output table'

# IAM
alias oci-whoami='oci iam user get --user-id $(grep ^user ~/.oci/config | head -1 | cut -d= -f2) --query "data.{Name:name,Email:email}" --output table'

# Health check
alias oci-health='oci iam region list --output table && echo "OCI connectivity OK"'
```

### Step 5: Common CLI Workflows

**List and filter resources with JMESPath queries:**

```bash
# Instances by shape
oci compute instance list --compartment-id $OCI_COMPARTMENT_ID \
  --query "data[?shape=='VM.Standard.A1.Flex'].{Name:\"display-name\",State:\"lifecycle-state\"}" \
  --output table

# Buckets with size (requires additional call per bucket)
oci os bucket list --compartment-id $OCI_COMPARTMENT_ID \
  --query "data[*].name" --raw-output

# Find an image by name
oci compute image list --compartment-id $OCI_COMPARTMENT_ID \
  --query "data[?contains(\"display-name\", 'Oracle-Linux-8')].{Name:\"display-name\",ID:id}" \
  --output table --limit 5
```

**Instance lifecycle from CLI:**

```bash
# Launch instance
oci compute instance launch \
  --compartment-id $OCI_COMPARTMENT_ID \
  --availability-domain "Uocm:US-ASHBURN-AD-1" \
  --shape "VM.Standard.E4.Flex" \
  --shape-config '{"ocpus": 1, "memoryInGBs": 8}' \
  --display-name "dev-instance" \
  --image-id <IMAGE_OCID> \
  --subnet-id <SUBNET_OCID> \
  --ssh-authorized-keys-file ~/.ssh/id_rsa.pub

# Stop / start / terminate
oci compute instance action --instance-id <OCID> --action STOP
oci compute instance action --instance-id <OCID> --action START
oci compute instance terminate --instance-id <OCID> --force
```

**Object storage operations:**

```bash
# Upload a file
oci os object put --bucket-name my-bucket --file ./data.csv --name data/input.csv

# Download a file
oci os object get --bucket-name my-bucket --name data/input.csv --file ./downloaded.csv

# List objects with prefix
oci os object list --bucket-name my-bucket --prefix "data/" \
  --query "data[*].{Name:name,Size:size}" --output table

# Bulk upload a directory
oci os object bulk-upload --bucket-name my-bucket --src-dir ./upload/ --overwrite
```

### Step 6: Python SDK Local Dev Script

Create a reusable dev helper:

```python
#!/usr/bin/env python3
"""oci_dev.py — Local OCI development helper."""

import oci
import os
import sys

def get_config(profile="DEFAULT"):
    """Load OCI config with environment variable overrides."""
    config = oci.config.from_file("~/.oci/config", profile_name=profile)
    # Allow env var override for compartment
    config["compartment_id"] = os.environ.get(
        "OCI_COMPARTMENT_ID", config.get("tenancy")
    )
    oci.config.validate_config(config)
    return config

def list_instances(config):
    compute = oci.core.ComputeClient(config, timeout=(10, 30))
    instances = compute.list_instances(
        compartment_id=config["compartment_id"]
    ).data
    for inst in instances:
        print(f"{inst.display_name:<30} {inst.lifecycle_state:<12} {inst.shape}")
    return instances

def list_buckets(config):
    os_client = oci.object_storage.ObjectStorageClient(config, timeout=(10, 30))
    namespace = os_client.get_namespace().data
    buckets = os_client.list_buckets(
        namespace_name=namespace,
        compartment_id=config["compartment_id"]
    ).data
    for b in buckets:
        print(f"{b.name:<40} {b.time_created}")
    return buckets

def health_check(config):
    identity = oci.identity.IdentityClient(config, timeout=(5, 15))
    user = identity.get_user(config["user"]).data
    regions = identity.list_regions().data
    print(f"User: {user.name}")
    print(f"Regions: {len(regions)} available")
    print("Status: OK")

if __name__ == "__main__":
    profile = os.environ.get("OCI_CLI_PROFILE", "DEFAULT")
    cfg = get_config(profile)

    cmd = sys.argv[1] if len(sys.argv) > 1 else "health"
    if cmd == "instances":
        list_instances(cfg)
    elif cmd == "buckets":
        list_buckets(cfg)
    elif cmd == "health":
        health_check(cfg)
    else:
        print(f"Usage: python oci_dev.py [instances|buckets|health]")
```

```bash
# Usage
python oci_dev.py health
python oci_dev.py instances
OCI_CLI_PROFILE=dev python oci_dev.py buckets
```

### Step 7: Project Structure

```
my-oci-project/
├── .env                    # OCI_COMPARTMENT_ID, OCI_REGION, OCI_CLI_PROFILE
├── .gitignore              # .env, *.pem, ~/.oci/
├── oci_dev.py              # Dev helper script (Step 6)
├── src/
│   └── oci_client.py       # Singleton client (see oraclecloud-sdk-patterns)
├── scripts/
│   ├── setup.sh            # Install oci + oci-cli + source .env
│   └── teardown.sh         # Terminate dev resources
└── tests/
    └── test_oci.py         # Unit tests with mocked OCI responses
```

## Output

Successful setup produces:
- OCI CLI installed and verified with `oci iam region list`
- Multi-profile `~/.oci/config` for dev/staging/prod switching
- Shell aliases for common OCI operations (instances, buckets, health)
- A reusable Python dev helper script for listing resources and health checks
- Environment variable management via `.env` for project-specific OCIDs

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Wrong profile or expired key | Check `OCI_CLI_PROFILE` matches a valid config section |
| NotAuthorizedOrNotFound | 404 | Compartment OCID wrong for this profile | Verify `OCI_COMPARTMENT_ID` matches the profile's tenancy |
| ConfigFileNotFound | — | `~/.oci/config` missing | Run `oraclecloud-install-auth` |
| command not found: oci | — | OCI CLI not installed | `pip install oci-cli` |
| TooManyRequests | 429 | Rapid CLI commands hitting rate limit | Add `--retry-strategy default` or space out requests |
| ServiceError status -1 | -1 | Network timeout | Check connectivity; increase timeout in SDK scripts |

## Examples

**One-liner resource summary:**

```bash
echo "=== OCI Status ===" && \
oci-health && \
echo "Instances:" && oci-instances && \
echo "Buckets:" && oci-buckets
```

**Switch profile and list resources in one command:**

```bash
OCI_CLI_PROFILE=dev oci compute instance list \
  --compartment-id $OCI_COMPARTMENT_ID --output table
```

## Resources

- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — full command reference and configuration guide
- [OCI CLI Configuration](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm) — config file format and profiles
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — API documentation for all service clients
- [OCI API Reference](https://docs.oracle.com/en-us/iaas/api/) — REST API endpoints and schemas
- [OCI Terraform Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs) — infrastructure as code alternative
- [OCI Status](https://ocistatus.oraclecloud.com) — service health dashboard

## Next Steps

With your local dev loop set up, see `oraclecloud-sdk-patterns` for production-grade client patterns, or `oraclecloud-common-errors` when you hit issues during development.
