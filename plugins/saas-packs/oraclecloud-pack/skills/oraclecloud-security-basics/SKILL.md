---
name: oraclecloud-security-basics
description: 'Master OCI IAM policy syntax, common policy patterns, and API key management.

  Use when writing IAM policies, granting access to compartments, or managing API
  keys.

  Trigger with "oraclecloud security basics", "oci iam policy", "oci policy syntax",
  "oci api key setup".

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
# Oracle Cloud Security Basics

## Overview

OCI IAM policy syntax (`Allow group X to manage Y in compartment Z`) is the number one enterprise complaint. One wrong policy locks you out of your own resources. One missing verb and your automation silently fails with a `404 NotAuthorizedOrNotFound` that looks like a missing resource. This skill is the IAM policy cheat sheet with tested patterns for common access scenarios.

**Purpose:** Write correct IAM policies, manage API keys securely, and understand the OCI permission model.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **OCI config file** at `~/.oci/config` with valid credentials (user, fingerprint, tenancy, region, key_file)
- **Tenancy administrator access** (to create policies) or membership in a group with `manage policies` permission
- Python 3.8+

## Instructions

### Step 1: Understand the Policy Verb Hierarchy

OCI uses four verbs in ascending order of privilege. Each higher verb includes all lower verbs:

| Verb | Capabilities | Typical Use Case |
|------|-------------|------------------|
| `inspect` | List resources, get metadata only | Auditors, read-only dashboards |
| `read` | Inspect + get full resource details/contents | Monitoring tools, reporting |
| `use` | Read + act on existing resources (start/stop, attach) | Developers, operators |
| `manage` | Use + create, delete, move resources | Admins, automation service accounts |

**Critical:** `use` does NOT include `create` or `delete`. This trips up every new OCI team.

### Step 2: IAM Policy Syntax

Every OCI policy statement follows this exact structure:

```
Allow <subject> to <verb> <resource-type> in <location> [where <conditions>]
```

**Subject types:**
- `group <group-name>` — IAM user group
- `dynamic-group <dg-name>` — resource principals (instances, functions)
- `any-user` — every authenticated user (use with extreme caution)

**Location types:**
- `tenancy` — entire tenancy (root-level policy only)
- `compartment <name>` — specific compartment
- `compartment id <ocid>` — by OCID (for automation)

### Step 3: Common Policy Patterns

Copy these tested patterns directly. Replace group names and compartment names with your values:

```python
import oci

config = oci.config.from_file("~/.oci/config")
identity = oci.identity.IdentityClient(config)

# Create a policy with multiple statements
tenancy_id = config["tenancy"]

# --- Pattern 1: Full admin for a compartment ---
admin_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,
        name="compartment-admins",
        description="Full admin access to the dev compartment",
        statements=[
            "Allow group DevAdmins to manage all-resources in compartment dev"
        ]
    )
)

# --- Pattern 2: Read-only access (auditors) ---
readonly_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,
        name="auditor-readonly",
        description="Read-only access for auditors",
        statements=[
            "Allow group Auditors to read all-resources in compartment prod"
        ]
    )
)

# --- Pattern 3: Compute-only operators ---
compute_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,
        name="compute-operators",
        description="Manage compute, read networking",
        statements=[
            "Allow group ComputeOps to manage instance-family in compartment prod",
            "Allow group ComputeOps to use virtual-network-family in compartment prod",
            "Allow group ComputeOps to read volume-family in compartment prod"
        ]
    )
)

# --- Pattern 4: Network admins ---
network_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,
        name="network-admins",
        description="Network management only",
        statements=[
            "Allow group NetAdmins to manage virtual-network-family in compartment prod",
            "Allow group NetAdmins to manage load-balancers in compartment prod",
            "Allow group NetAdmins to read instance-family in compartment prod"
        ]
    )
)

# --- Pattern 5: Restrict deletes (protect production) ---
no_delete_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,
        name="no-delete-prod",
        description="Allow manage but block deletes in production",
        statements=[
            "Allow group DevOps to manage all-resources in compartment prod where request.permission != 'INSTANCE_DELETE'",
            "Allow group DevOps to manage all-resources in compartment prod where request.permission != 'BUCKET_DELETE'"
        ]
    )
)
print("Policies created successfully")
```

### Step 4: Key Resource Family Types

Policies use resource families, not individual resource types:

| Resource Family | Includes |
|----------------|----------|
| `all-resources` | Everything (use sparingly) |
| `instance-family` | Instances, instance configurations, instance pools |
| `volume-family` | Block volumes, volume backups, volume groups |
| `virtual-network-family` | VCNs, subnets, route tables, security lists, NSGs |
| `object-family` | Buckets, objects, pre-authenticated requests |
| `database-family` | DB systems, autonomous databases, backups |
| `load-balancers` | Load balancers, backend sets, listeners |
| `function-family` | Functions, applications, invocations |
| `cluster-family` | OKE clusters, node pools |

### Step 5: API Key Management

Generate and upload API keys for secure programmatic access:

```bash
# Generate a 2048-bit RSA key pair
mkdir -p ~/.oci
openssl genrsa -out ~/.oci/oci_api_key.pem 2048
chmod 600 ~/.oci/oci_api_key.pem

# Extract the public key (upload this to OCI Console)
openssl rsa -pubout -in ~/.oci/oci_api_key.pem -out ~/.oci/oci_api_key_public.pem

# Get the key fingerprint (needed for ~/.oci/config)
openssl rsa -pubout -outform DER -in ~/.oci/oci_api_key.pem | openssl md5 -c
```

Upload the public key in OCI Console: **Identity > Users > Your User > API Keys > Add API Key**.

### Step 6: Configure ~/.oci/config

```ini
[DEFAULT]
user=ocid1.user.oc1..exampleuniqueID
fingerprint=aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99
tenancy=ocid1.tenancy.oc1..exampleuniqueID
region=us-ashburn-1
key_file=~/.oci/oci_api_key.pem
```

Verify the config:

```python
import oci

config = oci.config.from_file("~/.oci/config")
oci.config.validate_config(config)

identity = oci.identity.IdentityClient(config)
user = identity.get_user(config["user"]).data
print(f"Authenticated as: {user.name} ({user.email})")
```

## Output

Successful completion produces:
- IAM policies granting appropriate access levels per group/role
- An API key pair with the public key uploaded to OCI Console
- A validated `~/.oci/config` file with correct user, fingerprint, tenancy, region, and key_file
- Verified authentication confirmed by a successful Identity API call

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Bad API key, wrong fingerprint, or expired key | Regenerate key pair and re-upload public key |
| NotAuthorizedOrNotFound | 404 | Missing IAM policy — OCI returns 404, not 403 | Add policy for the group/resource/compartment |
| InvalidParameter | 400 | Policy syntax error | Check verb, resource-type, and compartment name spelling |
| TooManyRequests | 429 | Rate limited on Identity API | Back off; Identity has ~10 req/sec limit |
| InternalError | 500 | OCI service error | Retry after 30s; check https://ocistatus.oraclecloud.com |
| CERTIFICATE_VERIFY_FAILED | — | SSL certificate issue | Update CA certificates: `pip install certifi` |

**Important:** OCI returns `404 NotAuthorizedOrNotFound` for both "resource doesn't exist" and "you don't have permission." Always check IAM policies first.

## Examples

**List all policies in a compartment:**

```python
import oci

config = oci.config.from_file("~/.oci/config")
identity = oci.identity.IdentityClient(config)

policies = identity.list_policies(compartment_id=config["tenancy"]).data
for p in policies:
    print(f"\n{p.name}:")
    for stmt in p.statements:
        print(f"  {stmt}")
```

**Quick policy validation via CLI:**

```bash
# List all policies in the tenancy root
oci iam policy list --compartment-id <tenancy-ocid> --all

# Check what a specific group can do
oci iam policy list --compartment-id <tenancy-ocid> --all \
  | python3 -c "import sys,json; [print(s) for p in json.load(sys.stdin)['data'] for s in p['statements'] if 'DevOps' in s]"
```

## Resources

- [IAM Policy Reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/policyreference.htm) — complete verb and resource-type list
- [IAM Policy Syntax](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policysyntax.htm) — syntax rules and conditions
- [Common Policies](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm) — Oracle's recommended patterns
- [API Key Management](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/apisigningkey.htm) — key generation and upload
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — IdentityClient API

## Next Steps

After IAM policies are in place, see `oraclecloud-enterprise-rbac` for compartment hierarchy design and dynamic groups, or `oraclecloud-multi-env-setup` for profile-based environment separation.
