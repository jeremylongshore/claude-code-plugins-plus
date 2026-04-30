---
name: oraclecloud-multi-env-setup
description: 'Configure multi-environment OCI workflows with config profiles and compartment-per-environment
  patterns.

  Use when setting up dev/staging/prod separation, switching between OCI profiles,
  or preventing accidental production deployments.

  Trigger with "oraclecloud multi env setup", "oci profiles", "oci environments",
  "oci config profiles".

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
# Oracle Cloud Multi-Environment Setup

## Overview

OCI has no "accounts" like AWS — you use compartments plus OCI config profiles for dev/staging/prod separation. But profile switching is manual, compartment OCIDs are easy to confuse, and one wrong `--compartment-id` deploys to production. This skill sets up safe multi-environment workflows with named profiles, compartment aliasing, environment validation, and deployment guardrails.

**Purpose:** Configure safe, repeatable multi-environment OCI workflows that prevent accidental cross-environment operations.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **OCI CLI** — installed and configured (`oci setup config`)
- **Separate API keys per environment** (recommended) or a single key with cross-compartment policies
- **Compartment OCIDs** for each environment (dev, staging, prod)
- Python 3.8+

## Instructions

### Step 1: Configure Multi-Profile ~/.oci/config

The OCI config file supports named profiles. Each profile can point to different tenancies, regions, or use different API keys:

```ini
# ~/.oci/config

[DEFAULT]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem

[DEV]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=us-ashburn-1
key_file=~/.oci/oci_api_key_dev.pem

[STAGING]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=11:22:33:44:55:66:77:88:99:aa:bb:cc:dd:ee:ff:00
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=us-phoenix-1
key_file=~/.oci/oci_api_key_staging.pem

[PROD]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=ff:ee:dd:cc:bb:aa:00:99:88:77:66:55:44:33:22:11
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=us-ashburn-1
key_file=~/.oci/oci_api_key_prod.pem
```

**Best practice:** Use different API key pairs per environment. If the dev key is compromised, prod is unaffected.

### Step 2: Create an Environment Configuration Module

Centralize compartment OCIDs and profile mappings to prevent OCID confusion:

```python
import oci
import os

# Environment configuration — single source of truth for OCIDs
ENVIRONMENTS = {
    "dev": {
        "profile": "DEV",
        "compartment_id": "ocid1.compartment.oc1..dev_example",
        "region": "us-ashburn-1",
        "allow_destructive": True,
    },
    "staging": {
        "profile": "STAGING",
        "compartment_id": "ocid1.compartment.oc1..staging_example",
        "region": "us-phoenix-1",
        "allow_destructive": True,
    },
    "prod": {
        "profile": "PROD",
        "compartment_id": "ocid1.compartment.oc1..prod_example",
        "region": "us-ashburn-1",
        "allow_destructive": False,  # Safety: block destructive ops
    },
}

def get_oci_config(env_name):
    """Load OCI config for the specified environment.

    Validates the environment name and returns a configured
    OCI config dict ready for client construction.
    """
    if env_name not in ENVIRONMENTS:
        raise ValueError(
            f"Unknown environment: {env_name}. "
            f"Valid: {list(ENVIRONMENTS.keys())}"
        )

    env = ENVIRONMENTS[env_name]
    config = oci.config.from_file("~/.oci/config", profile_name=env["profile"])
    oci.config.validate_config(config)
    return config, env

def get_compartment_id(env_name):
    """Get the compartment OCID for an environment."""
    return ENVIRONMENTS[env_name]["compartment_id"]

def is_destructive_allowed(env_name):
    """Check if destructive operations are allowed in this environment."""
    return ENVIRONMENTS[env_name]["allow_destructive"]
```

### Step 3: Build Safe Environment-Aware Clients

Wrap OCI clients with environment validation to prevent cross-environment mistakes:

```python
import oci
import sys

class OCIEnvironment:
    """Environment-aware OCI client factory with safety guardrails."""

    def __init__(self, env_name):
        self.env_name = env_name
        self.config, self.env = get_oci_config(env_name)
        self.compartment_id = self.env["compartment_id"]

        # Verify we can authenticate
        identity = oci.identity.IdentityClient(self.config)
        user = identity.get_user(self.config["user"]).data
        print(f"[{env_name.upper()}] Authenticated as {user.name} "
              f"in {self.config['region']}")

    def compute(self):
        return oci.core.ComputeClient(self.config)

    def network(self):
        return oci.core.VirtualNetworkClient(self.config)

    def storage(self):
        return oci.object_storage.ObjectStorageClient(self.config)

    def database(self):
        return oci.database.DatabaseClient(self.config)

    def safe_delete(self, operation, resource_name):
        """Execute a delete operation with environment safety checks."""
        if not is_destructive_allowed(self.env_name):
            print(f"BLOCKED: Destructive operation on {resource_name} "
                  f"not allowed in {self.env_name.upper()}")
            print("Set allow_destructive=True in ENVIRONMENTS to override")
            sys.exit(1)

        print(f"WARNING: Deleting {resource_name} in {self.env_name.upper()}")
        return operation()

# Usage
dev = OCIEnvironment("dev")
instances = dev.compute().list_instances(compartment_id=dev.compartment_id).data
print(f"Dev instances: {len(instances)}")

prod = OCIEnvironment("prod")
# prod.safe_delete(...) would be blocked by allow_destructive=False
```

### Step 4: CLI Profile Switching

Use profiles with the OCI CLI to target specific environments:

```bash
# List instances in dev
oci compute instance list --compartment-id ocid1.compartment.oc1..dev_example --profile DEV

# List instances in prod (read-only)
oci compute instance list --compartment-id ocid1.compartment.oc1..prod_example --profile PROD

# Set default profile via environment variable
export OCI_CLI_PROFILE=DEV

# Override per-command
OCI_CLI_PROFILE=PROD oci compute instance list --compartment-id ocid1.compartment.oc1..prod_example
```

**Shell aliases for safety:**

```bash
# Add to ~/.bashrc or ~/.zshrc
alias oci-dev='OCI_CLI_PROFILE=DEV oci'
alias oci-staging='OCI_CLI_PROFILE=STAGING oci'
alias oci-prod='OCI_CLI_PROFILE=PROD oci'

# Usage
oci-dev compute instance list --compartment-id ocid1.compartment.oc1..dev_example
oci-prod compute instance list --compartment-id ocid1.compartment.oc1..prod_example
```

### Step 5: Validate Config Before Operations

Always validate the config file and profile before running automation:

```python
import oci

def validate_all_profiles():
    """Validate all OCI config profiles are properly configured."""
    profiles = ["DEFAULT", "DEV", "STAGING", "PROD"]
    results = {}

    for profile in profiles:
        try:
            config = oci.config.from_file("~/.oci/config", profile_name=profile)
            oci.config.validate_config(config)

            # Test authentication
            identity = oci.identity.IdentityClient(config)
            user = identity.get_user(config["user"]).data
            results[profile] = f"OK — {user.name} in {config['region']}"
        except oci.exceptions.ConfigFileNotFound:
            results[profile] = "FAIL — config file not found"
        except oci.exceptions.ProfileNotFound:
            results[profile] = "FAIL — profile not found in config"
        except oci.exceptions.ServiceError as e:
            results[profile] = f"FAIL — {e.status}: {e.code}"
        except Exception as e:
            results[profile] = f"FAIL — {str(e)}"

    print("OCI Profile Validation:")
    for profile, status in results.items():
        print(f"  [{profile}] {status}")

    return all("OK" in s for s in results.values())

validate_all_profiles()
```

### Step 6: Environment Variables for CI/CD

For CI/CD pipelines where config files are impractical, use environment variables:

```bash
# Set OCI config via environment variables (CI/CD pipelines)
export OCI_CLI_USER="ocid1.user.oc1..exampleuniqueID"
export OCI_CLI_FINGERPRINT="aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99"
export OCI_CLI_TENANCY="ocid1.tenancy.oc1..exampleuniqueID"
export OCI_CLI_REGION="us-ashburn-1"
export OCI_CLI_KEY_FILE="/path/to/key.pem"
# Or use key content directly:
export OCI_CLI_KEY_CONTENT="-----BEGIN RSA PRIVATE KEY-----\n..."
```

```python
import oci

# Python SDK reads from environment when no config file exists
config = oci.config.from_file()  # Falls back to env vars if ~/.oci/config missing

# Or construct config dict directly for CI/CD
config = {
    "user": os.environ["OCI_CLI_USER"],
    "fingerprint": os.environ["OCI_CLI_FINGERPRINT"],
    "tenancy": os.environ["OCI_CLI_TENANCY"],
    "region": os.environ["OCI_CLI_REGION"],
    "key_file": os.environ["OCI_CLI_KEY_FILE"],
}
oci.config.validate_config(config)
```

## Output

Successful completion produces:
- A `~/.oci/config` file with named profiles for each environment (DEV, STAGING, PROD)
- An environment configuration module mapping profiles to compartment OCIDs
- An environment-aware client factory with safety guardrails blocking destructive prod operations
- Shell aliases for safe CLI profile switching
- Validated authentication for all profiles

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| ProfileNotFound | — | Wrong profile name in `from_file()` | Check `~/.oci/config` profile names match exactly (case-sensitive) |
| ConfigFileNotFound | — | Missing `~/.oci/config` | Run `oci setup config` or create the file manually |
| NotAuthenticated | 401 | Wrong key for the selected profile | Verify key_file path and fingerprint match the uploaded public key |
| NotAuthorizedOrNotFound | 404 | Profile's user lacks access to target compartment | Add IAM policies for the user/group in the target compartment |
| TooManyRequests | 429 | Rate limited | Back off; see `oraclecloud-rate-limits` |
| InternalError | 500 | OCI service error | Retry after 30s; check https://ocistatus.oraclecloud.com |

**Critical mistake:** Using the DEFAULT profile's compartment OCID with the PROD profile's credentials (or vice versa). The environment config module in Step 2 prevents this by coupling profile names to compartment OCIDs.

## Examples

**Quick profile test from the command line:**

```bash
# Test all profiles in one shot
for profile in DEFAULT DEV STAGING PROD; do
  echo -n "[$profile] "
  oci iam user get --user-id "$(oci iam user list --profile "$profile" --query 'data[0].id' --raw-output 2>/dev/null)" --profile "$profile" --query 'data.name' --raw-output 2>/dev/null || echo "FAILED"
done
```

**Check which profile is active:**

```python
import oci
import os

profile = os.environ.get("OCI_CLI_PROFILE", "DEFAULT")
config = oci.config.from_file("~/.oci/config", profile_name=profile)
print(f"Active profile: {profile}")
print(f"Region: {config['region']}")
print(f"Tenancy: {config['tenancy']}")
```

## Resources

- [OCI Config File](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdkconfig.htm) — config file format and profile syntax
- [CLI Environment Variables](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm) — OCI_CLI_* variables
- [CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — command-line interface guide
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — config loading and client construction
- [Compartment Management](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm) — organizing resources by environment

## Next Steps

After environments are configured, see `oraclecloud-enterprise-rbac` for compartment hierarchy design with least-privilege policies, or `oraclecloud-deploy-integration` for CI/CD pipeline integration.
