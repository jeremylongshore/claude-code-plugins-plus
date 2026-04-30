---
name: oraclecloud-install-auth
description: 'Install and configure Oracle Cloud Infrastructure (OCI) SDK and CLI
  authentication.

  Use when setting up a new OCI integration, generating API signing keys, or debugging
  config file errors.

  Trigger with "install oraclecloud", "setup oci auth", "oraclecloud credentials",
  "oci config".

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
# Oracle Cloud Install & Auth

## Overview

Configure API key authentication for Oracle Cloud Infrastructure (OCI). OCI auth requires a `~/.oci/config` file with **five mandatory fields** — user OCID, fingerprint, tenancy OCID, region, and the path to an RSA private key. One wrong field produces the cryptic `ConfigFileNotFound` or `InvalidKeyFilePath` error with no hint about which field failed.

**Purpose:** Produce a validated `~/.oci/config` file, generate an RSA key pair, upload the public key to OCI, and verify connectivity with both the Python SDK and OCI CLI.

## Prerequisites

- **OCI account** with an active tenancy — sign up at https://cloud.oracle.com
- **Python 3.8+** (the OCI Python SDK is the most mature SDK)
- **OpenSSL** installed (for RSA key generation)
- Your **user OCID** (Profile > User Settings in the OCI Console) — format: `ocid1.user.oc1..aaaa...`
- Your **tenancy OCID** (Administration > Tenancy Details) — format: `ocid1.tenancy.oc1..aaaa...`
- Your **home region** (e.g., `us-ashburn-1`, `eu-frankfurt-1`)

## Instructions

### Step 1: Install the OCI Python SDK and CLI

```bash
pip install oci oci-cli
```

### Step 2: Generate an RSA Key Pair

```bash
mkdir -p ~/.oci
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
chmod 600 ~/.oci/oci_api_key.pem
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem
```

### Step 3: Get the Key Fingerprint

```bash
openssl rsa -pubout -outform DER -in ~/.oci/oci_api_key.pem | openssl md5 -c
# Output: ab:cd:ef:12:34:56:78:90:ab:cd:ef:12:34:56:78:90
```

### Step 4: Upload Public Key to OCI Console

Navigate to: **Profile (top-right) > User Settings > API Keys > Add API Key > Paste Public Key**

Paste the contents of `~/.oci/oci_api_key_public.pem`. The console shows the fingerprint — it must match Step 3.

### Step 5: Create the Config File

```bash
cat > ~/.oci/config << 'EOF'
[DEFAULT]
user=ocid1.user.oc1..aaaa_YOUR_USER_OCID
fingerprint=ab:cd:ef:12:34:56:78:90:ab:cd:ef:12:34:56:78:90
tenancy=ocid1.tenancy.oc1..aaaa_YOUR_TENANCY_OCID
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
EOF
chmod 600 ~/.oci/config
```

All five fields are required. The `key_file` must point to the **private** key (not the public `.pem`).

### Step 6: Verify with the Python SDK

```python
import oci

config = oci.config.from_file("~/.oci/config")
oci.config.validate_config(config)

identity = oci.identity.IdentityClient(config)
user = identity.get_user(config["user"]).data
print(f"Authenticated as: {user.name} ({user.email})")
print(f"Tenancy: {config['tenancy']}")
print(f"Region: {config['region']}")
```

### Step 7: Verify with the OCI CLI

```bash
oci iam user get --user-id "$(grep ^user ~/.oci/config | cut -d= -f2)" \
  --query 'data.name' --raw-output
```

### Step 8: Config Validation Script

Save this as `validate_oci_config.py` to catch common misconfigurations:

```python
import oci
import os

def validate():
    """Validate OCI config file and key access."""
    config_path = os.path.expanduser("~/.oci/config")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config not found: {config_path}")

    config = oci.config.from_file(config_path)
    oci.config.validate_config(config)

    key_path = os.path.expanduser(config.get("key_file", ""))
    if not os.path.exists(key_path):
        raise FileNotFoundError(f"Private key not found: {key_path}")

    perms = oct(os.stat(key_path).st_mode)[-3:]
    if perms != "600":
        print(f"WARNING: Key file permissions are {perms}, should be 600")

    identity = oci.identity.IdentityClient(config)
    identity.get_user(config["user"])
    print("Config is valid. Authentication successful.")

validate()
```

## Output

Successful completion produces:
- An RSA key pair at `~/.oci/oci_api_key.pem` (private) and `~/.oci/oci_api_key_public.pem` (public)
- A validated `~/.oci/config` with all five required fields
- The public key uploaded to your OCI user profile with a matching fingerprint
- Confirmed API connectivity via either the Python SDK or OCI CLI

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Wrong fingerprint or key mismatch | Verify fingerprint matches: `openssl rsa -pubout -outform DER -in ~/.oci/oci_api_key.pem \| openssl md5 -c` |
| ConfigFileNotFound | — | Missing `~/.oci/config` | Run `oci setup config` or create manually per Step 5 |
| InvalidKeyFilePath | — | `key_file` points to wrong path or public key | Ensure `key_file=~/.oci/oci_api_key.pem` (private key, no `_public`) |
| InvalidPrivateKey | — | Key file is the public key, not private | The private key starts with `-----BEGIN RSA PRIVATE KEY-----` |
| NotAuthorizedOrNotFound | 404 | User OCID is wrong or IAM policy missing | Double-check user OCID in Console > Profile > User Settings |
| CERTIFICATE_VERIFY_FAILED | — | SSL cert issue behind corporate proxy | Set `OCI_PYTHON_SDK_NO_SERVICE_IMPORTS=1` or install `certifi` |

## Examples

**Quick auth test with curl (no SDK needed):**

```bash
# Verify the OCI CLI can reach the API
oci iam region list --output table
```

**Multiple profiles for dev/staging/prod:**

```ini
# ~/.oci/config
[DEFAULT]
user=ocid1.user.oc1..aaaa_PROD_USER
tenancy=ocid1.tenancy.oc1..aaaa_PROD
region=us-ashburn-1
fingerprint=ab:cd:...
key_file=~/.oci/oci_api_key.pem

[STAGING]
user=ocid1.user.oc1..aaaa_STAGING_USER
tenancy=ocid1.tenancy.oc1..aaaa_STAGING
region=us-phoenix-1
fingerprint=12:34:...
key_file=~/.oci/oci_api_key_staging.pem
```

```python
# Load a specific profile
config = oci.config.from_file("~/.oci/config", profile_name="STAGING")
```

## Resources

- [OCI API Key Authentication](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm) — key generation and config file format
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — full API documentation
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — command-line interface guide
- [SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — common auth and connectivity issues
- [OCI Console](https://cloud.oracle.com) — web dashboard for key upload and OCID lookup
- [Always Free Tier](https://www.oracle.com/cloud/free/) — free OCI resources for development

## Next Steps

After authentication is working, proceed to `oraclecloud-hello-world` to launch your first compute instance, or see `oraclecloud-common-errors` if you hit authentication issues.
