---
name: oraclecloud-upgrade-migration
description: "Safely upgrade OCI Python SDK and Terraform provider \u2014 version\
  \ pinning, breaking change detection, and rollback.\nUse when upgrading oci pip\
  \ packages, updating the Terraform OCI provider, or debugging post-upgrade failures.\n\
  Trigger with \"oraclecloud upgrade\", \"oci sdk upgrade\", \"oci terraform provider\
  \ update\", \"oci version migration\".\n"
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(oci:*), Bash(terraform:*), Bash(python3:*),
  Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Upgrade & Migration

## Overview

OCI Terraform provider and Python SDK break backwards compatibility more often than AWS equivalents. The Terraform provider has had provider crashes on `terraform plan` after upgrades, deprecated resource types removed without migration paths, and schema changes that silently alter behavior. The Python SDK has had memory leak fixes that changed object lifecycle semantics and authentication class renames between minor versions. This skill tracks known breaking changes and provides safe upgrade patterns with version pinning, pre-upgrade testing, and rollback procedures.

**Purpose:** Upgrade OCI Python SDK and Terraform provider versions safely, detect breaking changes before they hit production, and roll back cleanly if an upgrade fails.

## Prerequisites

- **Python 3.8+** with the current OCI SDK installed — `pip show oci`
- **Terraform 1.5+** with the OCI provider — `terraform version`
- **OCI CLI** installed — `oci --version`
- **Git** for version control of infrastructure code
- **A test environment** — never upgrade directly in production
- Current `~/.oci/config` validated (see `oraclecloud-install-auth`)

## Instructions

### Step 1: Audit Current Versions

```bash
# Python SDK version
pip show oci | grep -E "^(Name|Version|Location)"
# Example: Version: 2.125.0

# OCI CLI version
oci --version
# Example: 3.41.0

# Terraform provider version
grep -A2 'oracle/oci' .terraform.lock.hcl 2>/dev/null || echo "No lock file found"
terraform providers
# Example: oracle/oci v5.46.0
```

```python
import oci
print(f"OCI SDK version: {oci.__version__}")
```

### Step 2: Check for Known Breaking Changes

**Python SDK known breaking changes:**

| Version | Breaking Change | Impact | Mitigation |
|---------|----------------|--------|------------|
| 2.120.0+ | `oci.retry` module refactored | Custom retry strategies may break | Update to `oci.retry.retry.RetryStrategyBuilder` |
| 2.115.0+ | `oci.config.validate_config()` stricter | Rejects configs with extra fields | Remove non-standard fields from `~/.oci/config` |
| 2.105.0+ | Composite operations return type changed | `.data` attribute structure changed | Check `.data` type assertions in your code |
| 2.90.0+ | `wait_for_state` deprecated on some clients | Direct `get_*` polling required | Use `oci.wait_until()` helper instead |

**Terraform provider known breaking changes:**

| Version | Breaking Change | Impact | Mitigation |
|---------|----------------|--------|------------|
| 5.40.0+ | `oci_core_instance` schema change | `source_details` block restructured | Run `terraform plan` before apply to detect drift |
| 5.30.0+ | Deprecated `oci_core_virtual_network` removed | Must use `oci_core_vcn` | Search-and-replace in all `.tf` files |
| 5.20.0+ | Provider crashes on `terraform plan` with certain instance configs | Segfault in provider binary | Pin to 5.19.x until hotfix release |
| 5.0.0 | Major version bump — multiple resources renamed | State file references break | Use `terraform state mv` for renamed resources |

### Step 3: Python SDK Safe Upgrade

```bash
# Step 3a: Pin current version as fallback
pip freeze | grep ^oci > requirements-oci-backup.txt
echo "Current version saved to requirements-oci-backup.txt"

# Step 3b: Create an isolated branch
git checkout -b upgrade/oci-sdk-$(date +%Y%m%d)

# Step 3c: Upgrade with version constraint
pip install --upgrade "oci>=2.125.0,<2.130.0"  # Constrain to minor range
pip show oci | grep Version
```

```python
# Step 3d: Run validation script
import oci

config = oci.config.from_file("~/.oci/config")
oci.config.validate_config(config)

# Test core client instantiation
identity = oci.identity.IdentityClient(config)
compute = oci.core.ComputeClient(config)
network = oci.core.VirtualNetworkClient(config)
storage = oci.object_storage.ObjectStorageClient(config)
database = oci.database.DatabaseClient(config)
monitoring = oci.monitoring.MonitoringClient(config)

# Verify each client can make a basic call
identity.list_regions()
print("IdentityClient: OK")

compute.list_instances(compartment_id=config["tenancy"], limit=1)
print("ComputeClient: OK")

network.list_vcns(compartment_id=config["tenancy"], limit=1)
print("VirtualNetworkClient: OK")

namespace = storage.get_namespace().data
print(f"ObjectStorageClient: OK (namespace={namespace})")

print(f"\nAll clients validated on oci=={oci.__version__}")
```

### Step 4: Terraform Provider Safe Upgrade

```bash
# Step 4a: Record current state
terraform version > terraform-version-backup.txt
cp .terraform.lock.hcl .terraform.lock.hcl.backup

# Step 4b: Pin provider version in required_providers
```

```hcl
# versions.tf — pin to specific minor version
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.46.0"  # Allows 5.46.x patches only
    }
  }
}
```

```bash
# Step 4c: Upgrade provider
terraform init -upgrade

# Step 4d: Run plan to detect breaking changes (NEVER skip this)
terraform plan -out=upgrade-plan.tfplan 2>&1 | tee upgrade-plan.log

# Step 4e: Check for unexpected changes
grep -E "(must be replaced|forces replacement|will be destroyed)" upgrade-plan.log
# If any resources are being replaced unexpectedly, STOP and investigate
```

### Step 5: Deprecation Detection Script

Scan your codebase for deprecated OCI resource types and SDK patterns:

```bash
#!/bin/bash
echo "=== Deprecated Terraform Resources ==="
grep -rn "oci_core_virtual_network" *.tf 2>/dev/null && echo "  DEPRECATED: Use oci_core_vcn" || echo "  None found"
grep -rn "oci_core_security_list" *.tf 2>/dev/null && echo "  WARNING: Prefer oci_core_network_security_group" || echo "  None found"

echo ""
echo "=== Deprecated Python SDK Patterns ==="
grep -rn "from oci.core import" *.py 2>/dev/null | grep -v "ComputeClient\|VirtualNetworkClient\|BlockstorageClient" && echo "  Check for deprecated imports" || echo "  None found"
grep -rn "wait_for_state" *.py 2>/dev/null && echo "  DEPRECATED: Use oci.wait_until() instead" || echo "  None found"
```

### Step 6: OCI CLI Upgrade

```bash
# Check current version
oci --version

# Upgrade via pip (OCI CLI is a Python package)
pip install --upgrade oci-cli

# Verify CLI still works after upgrade
oci iam region list --output table && echo "CLI upgrade: OK" || echo "CLI upgrade: FAILED"

# If CLI breaks, rollback
pip install oci-cli==3.41.0  # Replace with your backup version
```

### Step 7: Rollback Procedures

**Python SDK rollback:**

```bash
# Restore pinned version
pip install -r requirements-oci-backup.txt
pip show oci | grep Version
```

**Terraform provider rollback:**

```bash
# Restore lock file
cp .terraform.lock.hcl.backup .terraform.lock.hcl
terraform init

# Verify state is intact
terraform plan  # Should show no changes
```

**Git-level rollback:**

```bash
# Discard upgrade branch entirely
git checkout main
git branch -D upgrade/oci-sdk-$(date +%Y%m%d)
```

## Output

Successful completion produces:
- Version audit showing current OCI SDK, CLI, and Terraform provider versions
- Breaking change assessment against the known issues table
- Upgraded Python SDK with all core clients validated (Identity, Compute, Network, Storage, Database, Monitoring)
- Upgraded Terraform provider with a clean `terraform plan` showing no unexpected resource replacements
- Deprecation scan results for both Terraform resources and Python SDK patterns
- Backup files for rollback (`requirements-oci-backup.txt`, `.terraform.lock.hcl.backup`)

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| `ModuleNotFoundError: oci` | — | SDK uninstalled during upgrade | `pip install oci` — start upgrade process over |
| Terraform provider crash (segfault) | — | Known provider bug in certain versions | Pin to last known good version (check Terraform registry issues) |
| `terraform plan` shows unexpected replacements | — | Schema change in provider | Review the plan carefully; use `terraform state mv` if resources were renamed |
| NotAuthenticated | 401 | SDK upgrade changed auth behavior | Re-validate config: `python3 -c "import oci; oci.config.validate_config(oci.config.from_file())"` |
| CERTIFICATE_VERIFY_FAILED | — | New SDK version uses updated cert bundle | Install `certifi`: `pip install --upgrade certifi` |
| `terraform init` fails on lock file | — | Lock file hash mismatch after provider upgrade | Delete `.terraform.lock.hcl` and re-run `terraform init` |

## Examples

**Quick version check one-liner:**

```bash
echo "SDK: $(python3 -c 'import oci; print(oci.__version__)' 2>/dev/null || echo 'not installed')" && \
echo "CLI: $(oci --version 2>/dev/null || echo 'not installed')" && \
echo "TF: $(terraform version -json 2>/dev/null | python3 -c 'import sys,json; d=json.load(sys.stdin); [print(f"  {k}: {v}") for k,v in d.get("provider_selections",{}).items()]' || echo 'not installed')"
```

**Automated upgrade test script:**

```bash
#!/bin/bash
set -euo pipefail
echo "=== OCI Upgrade Test ==="
pip install --upgrade oci oci-cli
python3 -c "
import oci
config = oci.config.from_file()
oci.config.validate_config(config)
oci.identity.IdentityClient(config).list_regions()
print(f'SDK {oci.__version__}: PASS')
"
oci iam region list --output table > /dev/null && echo "CLI: PASS" || echo "CLI: FAIL"
echo "=== Done ==="
```

## Resources

- [OCI Python SDK Changelog](https://docs.oracle.com/en-us/iaas/tools/python/latest/changelog.html) — version-by-version changes
- [OCI Terraform Provider Releases](https://registry.terraform.io/providers/oracle/oci/latest/docs) — provider documentation and changelogs
- [OCI CLI Release Notes](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — CLI version history
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — full API documentation
- [SDK Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_troubleshooting.htm) — common upgrade and connectivity issues
- [OCI Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — platform-known issues affecting SDK/provider

## Next Steps

After upgrading, run `oraclecloud-prod-checklist` to verify the environment still passes all production checks, or see `oraclecloud-common-errors` for debugging any new error patterns introduced by the upgrade.
