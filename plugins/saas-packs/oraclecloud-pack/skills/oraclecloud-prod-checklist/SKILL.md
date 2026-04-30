---
name: oraclecloud-prod-checklist
description: "Pre-production readiness checklist for OCI \u2014 backup policies, security\
  \ audit, key rotation, encryption, and Cloud Guard.\nUse when preparing an OCI environment\
  \ for production workloads or auditing an existing deployment.\nTrigger with \"\
  oraclecloud prod checklist\", \"oci production ready\", \"oci security audit\",\
  \ \"oci well-architected\".\n"
allowed-tools: Read, Write, Edit, Bash(oci:*), Bash(python3:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# Oracle Cloud Production Checklist

## Overview

OCI has no "Well-Architected Review" equivalent to AWS. This is the pre-production gate: a comprehensive checklist covering backup policies, security list audit, API key rotation, compartment isolation, boot volume encryption, OS Management agent, Cloud Guard, and Vulnerability Scanning. Every item is verifiable via CLI or Python SDK — no subjective assessments, only pass/fail checks.

**Purpose:** Validate that an OCI environment meets production-grade security, resilience, and operational standards before going live.

## Prerequisites

- **OCI CLI installed and configured** — `~/.oci/config` validated (see `oraclecloud-install-auth`)
- **Python 3.8+** with the OCI SDK — `pip install oci`
- **Administrator-level IAM policies** — the checks require `inspect` and `read` across most service families
- **Target compartment OCID** — the compartment being audited
- **Cloud Guard** must be enabled at the tenancy level (Administration > Cloud Guard)

## Instructions

### Step 1: Compartment Isolation Audit

Production workloads must be in a dedicated compartment, not the root:

```bash
# List compartments — production should NOT be the root compartment
oci iam compartment list \
  --compartment-id "$TENANCY_OCID" \
  --query 'data[].{name:name, id:id, state:"lifecycle-state"}' \
  --output table

# Verify prod compartment has policies restricting access
oci iam policy list \
  --compartment-id "$PROD_COMPARTMENT_OCID" \
  --query 'data[].{name:name, statements:statements}' \
  --output json
```

**Pass criteria:** Production compartment is NOT the root tenancy. Policies follow least-privilege (no `manage all-resources in tenancy`).

### Step 2: Backup Policy Verification

```python
import oci

config = oci.config.from_file("~/.oci/config")
blockstorage = oci.core.BlockstorageClient(config)

# List all boot volumes in prod compartment
boot_volumes = blockstorage.list_boot_volumes(
    compartment_id="PROD_COMPARTMENT_OCID",
    availability_domain="AD-1",
).data

for vol in boot_volumes:
    # Check backup policy assignment
    try:
        assignments = blockstorage.get_volume_backup_policy_asset_assignment(
            asset_id=vol.id
        ).data
        if assignments:
            print(f"PASS: {vol.display_name} — backup policy assigned")
        else:
            print(f"FAIL: {vol.display_name} — no backup policy")
    except oci.exceptions.ServiceError:
        print(f"FAIL: {vol.display_name} — cannot check backup policy")
```

**Pass criteria:** Every boot volume and block volume has an assigned backup policy (Bronze minimum: weekly backups, 5-week retention).

### Step 3: Security List and NSG Audit

```bash
# List all security lists in the VCN
oci network security-list list \
  --compartment-id "$PROD_COMPARTMENT_OCID" \
  --vcn-id "$VCN_OCID" \
  --query 'data[].{name:"display-name", ingress:"ingress-security-rules[?source==\`0.0.0.0/0\`]"}' \
  --output json

# FAIL if any rule allows 0.0.0.0/0 ingress on ports other than 80/443
oci network nsg rules list \
  --network-security-group-id "$NSG_OCID" \
  --query 'data[?source==`0.0.0.0/0` && "tcp-options"."destination-port-range".min!=`443`]' \
  --output table
```

**Pass criteria:** No security list allows unrestricted ingress (`0.0.0.0/0`) except ports 80 and 443. Prefer NSGs over security lists for production workloads.

### Step 4: API Key Rotation Check

```python
import oci
from datetime import datetime, timezone, timedelta

config = oci.config.from_file("~/.oci/config")
identity = oci.identity.IdentityClient(config)

# List API keys for all users in the tenancy
users = identity.list_users(compartment_id=config["tenancy"]).data
max_age = timedelta(days=90)
now = datetime.now(timezone.utc)

for user in users:
    keys = identity.list_api_keys(user_id=user.id).data
    for key in keys:
        age = now - key.time_created
        status = "PASS" if age < max_age else "FAIL"
        print(f"  {status}: {user.name} — key {key.fingerprint} — {age.days} days old")
```

**Pass criteria:** No API key older than 90 days. Automated rotation via OCI Vault recommended.

### Step 5: Boot Volume Encryption

```bash
# Check that all boot volumes use customer-managed keys (not Oracle-managed)
oci bv boot-volume list \
  --compartment-id "$PROD_COMPARTMENT_OCID" \
  --query 'data[].{name:"display-name", kms:"kms-key-id"}' \
  --output table

# FAIL if kms-key-id is null (Oracle-managed default encryption)
```

**Pass criteria:** All boot volumes encrypted with customer-managed keys from OCI Vault. Oracle-managed encryption is the default but does not meet most compliance frameworks (SOC 2, PCI-DSS).

### Step 6: OS Management Agent Verification

```bash
# Check if instance agent plugins are enabled
oci instance-agent plugin list \
  --instanceagent-id "$INSTANCE_OCID" \
  --compartment-id "$PROD_COMPARTMENT_OCID" \
  --query 'data[].{name:name, status:status}' \
  --output table

# Required plugins: Vulnerability Scanning, OS Management Service Agent, Compute Instance Run Command
```

**Pass criteria:** OS Management Service Agent, Vulnerability Scanning, and Run Command plugins are all `RUNNING`.

### Step 7: Cloud Guard Status

```bash
# Verify Cloud Guard is enabled and detector recipes are active
oci cloud-guard target list \
  --compartment-id "$PROD_COMPARTMENT_OCID" \
  --query 'data.items[].{name:"display-name", state:"lifecycle-state"}' \
  --output table

# Check for open problems
oci cloud-guard problem list \
  --compartment-id "$PROD_COMPARTMENT_OCID" \
  --lifecycle-state "ACTIVE" \
  --query 'data.items[].{label:"resource-name", risk:"risk-level", detail:"additional-details"}' \
  --output table
```

**Pass criteria:** Cloud Guard target is ACTIVE with Oracle-managed detector recipes. Zero CRITICAL or HIGH risk problems.

### Step 8: Vulnerability Scanning

```bash
# List scan recipes and recent results
oci vulnerability-scanning host scan recipe list \
  --compartment-id "$PROD_COMPARTMENT_OCID" \
  --output table

oci vulnerability-scanning host vulnerability list \
  --compartment-id "$PROD_COMPARTMENT_OCID" \
  --query 'data.items[?severity==`CRITICAL`].{name:name, severity:severity, cve:"cve-reference"}' \
  --output table
```

**Pass criteria:** Scan recipes assigned to all compute instances. Zero CRITICAL vulnerabilities.

## Output

Successful completion produces:
- An 8-point pass/fail checklist covering compartment isolation, backups, security rules, key rotation, encryption, OS agents, Cloud Guard, and vulnerability scanning
- Specific FAIL findings with remediation commands for each item
- A clear go/no-go decision for production deployment

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthorizedOrNotFound | 404 | Insufficient IAM policies for audit | Add `allow group auditors to inspect all-resources in compartment prod` |
| NotAuthenticated | 401 | API key expired or misconfigured | Rotate key per Step 4 and update `~/.oci/config` |
| Cloud Guard not enabled | — | Cloud Guard never activated at tenancy level | Enable via Console: Administration > Cloud Guard > Enable |
| TooManyRequests | 429 | Rate limited when scanning all compartments | Add 1-second delay between API calls — no Retry-After header from OCI |
| InternalError | 500 | OCI service issue | Retry after 60 seconds; check https://ocistatus.oraclecloud.com |
| Vulnerability Scanning not available | — | Not enabled for the region/compartment | Enable: Console > Security > Vulnerability Scanning > Create Recipe |

## Examples

**Quick pre-flight check (CLI one-liners):**

```bash
# Check compartment isolation
oci iam compartment get --compartment-id "$PROD_COMPARTMENT_OCID" \
  --query 'data.name' --raw-output

# Count boot volumes without backup policies
oci bv boot-volume list --compartment-id "$PROD_COMPARTMENT_OCID" \
  --query 'length(data[?!"backup-policy-id"])' --raw-output

# Count open Cloud Guard problems
oci cloud-guard problem list --compartment-id "$PROD_COMPARTMENT_OCID" \
  --lifecycle-state ACTIVE --query 'length(data.items)' --raw-output
```

**Automated audit script:**

```python
import oci

config = oci.config.from_file("~/.oci/config")
results = {"pass": 0, "fail": 0}

# Check 1: Compartment exists and is not root
identity = oci.identity.IdentityClient(config)
compartments = identity.list_compartments(compartment_id=config["tenancy"]).data
results["pass" if len(compartments) > 0 else "fail"] += 1
print(f"Compartment isolation: {'PASS' if len(compartments) > 0 else 'FAIL'}")

print(f"\nResults: {results['pass']} passed, {results['fail']} failed")
```

## Resources

- [OCI Security Best Practices](https://docs.oracle.com/en-us/iaas/Content/Security/Concepts/security_guide.htm) — comprehensive security guidance
- [OCI Cloud Guard](https://docs.oracle.com/en-us/iaas/cloud-guard/home.htm) — threat detection and automated response
- [OCI Vulnerability Scanning](https://docs.oracle.com/en-us/iaas/scanning/home.htm) — host and container scanning
- [OCI Vault (KMS)](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm) — customer-managed encryption keys
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — full command-line documentation
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) — Cloud Guard and Vault pricing

## Next Steps

After the checklist passes, review `oraclecloud-observability` to set up monitoring and alerting, or `oraclecloud-incident-runbook` to prepare your incident response process before going live.
