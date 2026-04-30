---
name: oraclecloud-enterprise-rbac
description: 'Design OCI compartment hierarchies, dynamic groups, and cross-tenancy
  access patterns.

  Use when planning enterprise RBAC, setting up Instance Principal auth, or debugging
  policy inheritance.

  Trigger with "oraclecloud enterprise rbac", "oci compartments", "oci dynamic groups",
  "oci policy inheritance".

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
# Oracle Cloud Enterprise RBAC

## Overview

OCI compartments are powerful but the inheritance model is confusing. Policies at root vs compartment level behave differently, dynamic groups enable compute-to-service auth without API keys, and cross-tenancy access requires matching policies on both sides. Most teams get this wrong and over-permission everything with `manage all-resources in tenancy`. This skill designs proper compartment hierarchies with least-privilege access.

**Purpose:** Build a scalable, least-privilege OCI organization structure using compartments, policy inheritance, dynamic groups, and tag-based access control.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **OCI config file** at `~/.oci/config` with valid credentials (user, fingerprint, tenancy, region, key_file)
- **Tenancy administrator access** — compartment and policy creation requires root-level permissions
- Familiarity with OCI IAM basics (see `oraclecloud-security-basics` for policy syntax)
- Python 3.8+

## Instructions

### Step 1: Design the Compartment Hierarchy

OCI compartments are nested organizational units. Unlike AWS accounts, they share a single tenancy with inherited policies. A standard enterprise layout:

```
Root (Tenancy)
├── shared-infra          ← DNS, networking hub, shared services
├── security              ← Vault, audit logs, Cloud Guard
├── dev
│   ├── dev-compute       ← Dev instances, OKE clusters
│   └── dev-data          ← Dev databases, object storage
├── staging
│   ├── staging-compute
│   └── staging-data
└── prod
    ├── prod-compute
    └── prod-data
```

Create this hierarchy programmatically:

```python
import oci

config = oci.config.from_file("~/.oci/config")
identity = oci.identity.IdentityClient(config)
tenancy_id = config["tenancy"]

def create_compartment(parent_id, name, description):
    """Create a compartment and return its OCID."""
    result = identity.create_compartment(
        oci.identity.models.CreateCompartmentDetails(
            compartment_id=parent_id,
            name=name,
            description=description
        )
    )
    print(f"Created: {name} ({result.data.id})")
    return result.data.id

# Top-level compartments
shared = create_compartment(tenancy_id, "shared-infra", "Shared infrastructure services")
security = create_compartment(tenancy_id, "security", "Security and audit resources")
dev = create_compartment(tenancy_id, "dev", "Development environment")
staging = create_compartment(tenancy_id, "staging", "Staging environment")
prod = create_compartment(tenancy_id, "prod", "Production environment")

# Nested compartments
dev_compute = create_compartment(dev, "dev-compute", "Dev compute resources")
dev_data = create_compartment(dev, "dev-data", "Dev databases and storage")
prod_compute = create_compartment(prod, "prod-compute", "Prod compute resources")
prod_data = create_compartment(prod, "prod-data", "Prod databases and storage")
```

### Step 2: Understand Policy Inheritance Rules

Policy inheritance is the most misunderstood OCI concept. Three critical rules:

1. **Policies at root apply to all compartments below.** A policy `Allow group DevOps to manage all-resources in tenancy` grants access everywhere.

2. **Policies attached to a compartment only apply to that compartment and its children.** A policy attached to `dev` does NOT grant access to `prod`.

3. **Child compartments inherit parent permissions.** If `DevOps` can `manage instance-family in compartment dev`, they can also manage instances in `dev-compute` and `dev-data` (children of `dev`).

```python
# WRONG: Attaching at root gives access everywhere
# identity.create_policy(compartment_id=tenancy_id, statements=[
#     "Allow group DevOps to manage all-resources in tenancy"  # TOO BROAD
# ])

# RIGHT: Attach policies at the appropriate compartment level
# This policy is attached to the root but scoped to 'dev' compartment
dev_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,  # Policies must live at root or target compartment
        name="dev-team-access",
        description="Dev team full access to dev compartment only",
        statements=[
            "Allow group DevTeam to manage all-resources in compartment dev",
            "Allow group DevTeam to read all-resources in compartment shared-infra"
        ]
    )
)

# Prod access is separate and more restrictive
prod_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,
        name="prod-team-access",
        description="Prod team read + use, no delete",
        statements=[
            "Allow group ProdOps to use all-resources in compartment prod",
            "Allow group ProdOps to read all-resources in compartment shared-infra",
            "Allow group ProdOps to manage instance-family in compartment prod where request.permission != 'INSTANCE_DELETE'"
        ]
    )
)
```

### Step 3: Create Dynamic Groups for Instance Principal

Dynamic groups enable OCI instances and functions to authenticate to OCI services without API keys. This is the OCI equivalent of AWS IAM Roles for EC2:

```python
# Create a dynamic group matching all instances in the dev compartment
dynamic_group = identity.create_dynamic_group(
    oci.identity.models.CreateDynamicGroupDetails(
        compartment_id=tenancy_id,
        name="dev-instances",
        description="All compute instances in dev compartment",
        matching_rule="ANY {instance.compartment.id = 'ocid1.compartment.oc1..dev_ocid'}"
    )
)
print(f"Dynamic group: {dynamic_group.data.id}")

# Grant the dynamic group access to Object Storage
dg_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,
        name="dev-instances-object-storage",
        description="Let dev instances read/write object storage",
        statements=[
            "Allow dynamic-group dev-instances to manage object-family in compartment dev-data"
        ]
    )
)
```

**Dynamic group matching rules** support these predicates:
- `instance.compartment.id = '<ocid>'` — all instances in a compartment
- `instance.id = '<ocid>'` — specific instance
- `tag.<namespace>.<key>.value = '<value>'` — tag-based matching
- `ALL {rule1, rule2}` — must match all rules
- `ANY {rule1, rule2}` — must match at least one rule

### Step 4: Use Instance Principal Auth in Code

Inside an instance that belongs to a dynamic group, use Instance Principal instead of API keys:

```python
import oci

# On an OCI instance — no ~/.oci/config needed
signer = oci.auth.signers.InstancePrincipalsSecurityTokenSigner()
object_storage = oci.object_storage.ObjectStorageClient({}, signer=signer)

# List buckets (permissions come from dynamic group policies)
namespace = object_storage.get_namespace().data
buckets = object_storage.list_buckets(
    namespace_name=namespace,
    compartment_id="ocid1.compartment.oc1..dev_data_ocid"
)
for b in buckets.data:
    print(f"Bucket: {b.name}")
```

### Step 5: Tag-Based Access Control

Use defined tags for fine-grained access control across compartments:

```python
# Create a tag namespace and key for environment tagging
tag_namespace = identity.create_tag_namespace(
    oci.identity.models.CreateTagNamespaceDetails(
        compartment_id=tenancy_id,
        name="Operations",
        description="Operational tags for access control"
    )
)

identity.create_tag(
    tag_namespace.data.id,
    oci.identity.models.CreateTagDetails(
        name="Environment",
        description="Resource environment (dev, staging, prod)"
    )
)

# Policy using tag-based conditions
tag_policy = identity.create_policy(
    oci.identity.models.CreatePolicyDetails(
        compartment_id=tenancy_id,
        name="tag-based-access",
        description="Access controlled by environment tags",
        statements=[
            "Allow group DevTeam to manage all-resources in tenancy where target.resource.tag.Operations.Environment = 'dev'",
            "Allow group DevTeam to read all-resources in tenancy where target.resource.tag.Operations.Environment = 'prod'"
        ]
    )
)
```

## Output

Successful completion produces:
- A compartment hierarchy separating environments (dev/staging/prod) and concerns (compute/data/security)
- IAM policies attached at the correct level with least-privilege access per group
- Dynamic groups enabling Instance Principal auth for compute instances and functions
- Tag-based access control for cross-compartment fine-grained permissions

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthenticated | 401 | Bad config or API key | Verify `~/.oci/config` and key_file path |
| NotAuthorizedOrNotFound | 404 | Missing IAM policy or wrong compartment OCID | Policies must be at root for cross-compartment access |
| InvalidParameter | 400 | Policy syntax error or invalid matching rule | Check verb, resource-type, and dynamic group rule syntax |
| TooManyRequests | 429 | Identity API rate limit (~10 req/sec) | Back off; see `oraclecloud-rate-limits` |
| CompartmentAlreadyExists | 409 | Duplicate compartment name in same parent | Use a unique name or reuse the existing compartment |
| InternalError | 500 | OCI service error | Retry after 30s; check https://ocistatus.oraclecloud.com |

**Important:** Dynamic group changes take 5-10 minutes to propagate. If Instance Principal auth fails immediately after creating a dynamic group or policy, wait and retry.

## Examples

**List all compartments in a hierarchy:**

```python
import oci

config = oci.config.from_file("~/.oci/config")
identity = oci.identity.IdentityClient(config)

def print_hierarchy(parent_id, depth=0):
    compartments = identity.list_compartments(
        compartment_id=parent_id,
        lifecycle_state="ACTIVE"
    ).data
    for c in compartments:
        print(f"{'  ' * depth}{c.name} ({c.id})")
        print_hierarchy(c.id, depth + 1)

print_hierarchy(config["tenancy"])
```

**Quick audit of all dynamic groups:**

```bash
oci iam dynamic-group list --compartment-id <tenancy-ocid> --all \
  --query "data[].{name:name, rule:\"matching-rule\"}" --output table
```

## Resources

- [Compartment Management](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm) — creating and organizing compartments
- [Policy Inheritance](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policies.htm) — how policies inherit through the compartment tree
- [Dynamic Groups](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm) — matching rules and Instance Principal
- [Tag-Based Access Control](https://docs.oracle.com/en-us/iaas/Content/Tagging/Tasks/managingaccesswithtags.htm) — using defined tags in policies
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — IdentityClient API

## Next Steps

After the compartment hierarchy is in place, see `oraclecloud-multi-env-setup` for profile-based environment switching, or `oraclecloud-security-basics` for IAM policy syntax fundamentals.
