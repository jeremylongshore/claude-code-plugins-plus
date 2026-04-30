---
name: oraclecloud-migration-deep-dive
description: "Migrate workloads from AWS or Azure to OCI \u2014 IAM translation, networking\
  \ mapping, compute image import, and data migration.\nUse when planning an AWS-to-OCI\
  \ or Azure-to-OCI migration, translating cloud concepts, or importing custom images.\n\
  Trigger with \"oraclecloud migration\", \"aws to oci\", \"azure to oci\", \"oci\
  \ migration deep dive\".\n"
allowed-tools: Read, Write, Edit, Bash(oci:*), Bash(python3:*), Bash(terraform:*),
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
# Oracle Cloud Migration Deep Dive

## Overview

Migrating to OCI from AWS or Azure requires translating IAM concepts (roles to policies, accounts to compartments), networking (VPC to VCN, Security Groups to NSGs), and compute (AMI to custom image). OCI's migration tooling is underdocumented compared to AWS Migration Hub or Azure Migrate. This skill provides comprehensive concept mapping tables, custom image import procedures, network topology translation, IAM policy translation, and data migration patterns — everything needed for a controlled cloud migration.

**Purpose:** Translate AWS/Azure architecture into OCI equivalents and execute the migration using OCI CLI and Python SDK, with verification at each step.

## Prerequisites

- **OCI account** with an active tenancy — https://cloud.oracle.com
- **OCI CLI installed and configured** — `~/.oci/config` validated (see `oraclecloud-install-auth`)
- **Python 3.8+** with the OCI SDK — `pip install oci`
- **Source cloud CLI** — `aws` CLI or `az` CLI for exporting resources
- **Object Storage bucket** in OCI for staging image imports
- **IAM policies**: `manage objects in compartment`, `manage custom-images in compartment`, `manage virtual-network-family in compartment`

## Instructions

### Step 1: AWS-to-OCI Concept Mapping

| AWS Concept | OCI Equivalent | Key Differences |
|-------------|---------------|-----------------|
| Account | Tenancy | One tenancy = one billing entity, use compartments for isolation |
| Organization OU | Compartment | Compartments are hierarchical, up to 6 levels deep |
| IAM Role | IAM Policy | OCI policies use `allow group X to verb resource in compartment Y` syntax |
| IAM User | IAM User | Same concept, but OCI uses API key auth (not access keys) |
| VPC | VCN | VCN subnets are regional (not AZ-scoped like AWS) |
| Security Group | Network Security Group (NSG) | NSGs attach to VNICs, not instances. Also have Security Lists (subnet-level) |
| Route Table | Route Table | Similar, but OCI route rules target gateway OCIDs |
| Internet Gateway | Internet Gateway | Identical concept |
| NAT Gateway | NAT Gateway | Identical concept |
| VPC Endpoint | Service Gateway | Service Gateway routes to OCI services without internet |
| VPC Peering | LPG / DRG | LPG for same-region, DRG for cross-region or on-premises |
| AMI | Custom Image | Export as VMDK/QCOW2, import via Object Storage |
| EBS | Block Volume | Attachable block storage, similar performance tiers |
| S3 | Object Storage | Compatible API (S3 compatibility mode available) |
| RDS | Autonomous Database | Fully managed, but different administration model |
| EC2 Instance Type | Shape | Flex shapes allow fractional OCPU allocation |
| Availability Zone | Availability Domain (AD) | Same concept, 1-3 ADs per region |
| CloudWatch | Monitoring Service | Uses MQL (Monitoring Query Language) instead of CloudWatch metrics |
| CloudTrail | Audit Service | Automatic, no setup required |

### Step 2: Azure-to-OCI Concept Mapping

| Azure Concept | OCI Equivalent | Key Differences |
|---------------|---------------|-----------------|
| Subscription | Compartment | OCI uses compartments for billing isolation (not separate subscriptions) |
| Resource Group | Compartment | Compartments are hierarchical; resource groups are flat |
| Azure AD | OCI IAM / IDCS | OCI Identity Domains replaces IDCS for SSO/federation |
| VNet | VCN | OCI subnets are regional, not tied to a zone |
| NSG | NSG | Nearly identical concept |
| Azure SQL | Autonomous Database | Different scaling model (OCPU-based) |
| Managed Disk | Block Volume | Similar, but OCI uses volume groups for snapshots |
| Blob Storage | Object Storage | Different API, but S3-compatible mode available |
| Azure Monitor | Monitoring Service | MQL query language instead of Kusto |
| Azure Policy | Cloud Guard | Detective controls, not preventive like Azure Policy |

### Step 3: Custom Image Import (AWS AMI to OCI)

Export the AMI from AWS, then import to OCI via Object Storage:

```bash
# Step 3a: Export AMI from AWS as VMDK
aws ec2 create-store-image-task \
  --image-id ami-0123456789abcdef0 \
  --bucket my-export-bucket

# Step 3b: Download and upload to OCI Object Storage
aws s3 cp s3://my-export-bucket/ami-0123456789abcdef0.vmdk ./image.vmdk

oci os object put \
  --bucket-name migration-staging \
  --file ./image.vmdk \
  --name "imported-image.vmdk" \
  --namespace "$NAMESPACE"
```

```python
import oci

config = oci.config.from_file("~/.oci/config")
compute = oci.core.ComputeClient(config)

# Step 3c: Import as OCI custom image
image = compute.create_image(
    oci.core.models.CreateImageDetails(
        compartment_id="COMPARTMENT_OCID",
        display_name="migrated-from-aws",
        image_source_details=oci.core.models.ImageSourceViaObjectStorageTupleDetails(
            source_type="objectStorageTuple",
            bucket_name="migration-staging",
            namespace_name="NAMESPACE",
            object_name="imported-image.vmdk",
            source_image_type="VMDK",
        ),
    )
).data

print(f"Image import started: {image.id}")
print(f"State: {image.lifecycle_state}")  # IMPORTING → AVAILABLE
```

### Step 4: IAM Policy Translation

AWS IAM roles use JSON policies attached to entities. OCI uses human-readable policy statements attached to compartments:

```
# AWS: Allow EC2 instances to read S3
{
  "Effect": "Allow",
  "Action": ["s3:GetObject", "s3:ListBucket"],
  "Resource": "arn:aws:s3:::my-bucket/*"
}

# OCI equivalent:
allow dynamic-group app-instances to read objects in compartment prod where target.bucket.name='my-bucket'
```

Common IAM translations:

| AWS Policy | OCI Policy Statement |
|------------|---------------------|
| `AdministratorAccess` | `allow group admins to manage all-resources in tenancy` |
| `ReadOnlyAccess` | `allow group readers to inspect all-resources in tenancy` |
| `AmazonEC2FullAccess` | `allow group compute-admins to manage instances in compartment prod` |
| `AmazonS3ReadOnlyAccess` | `allow group readers to read objects in compartment prod` |
| `AmazonVPCFullAccess` | `allow group net-admins to manage virtual-network-family in compartment prod` |

```bash
# Create an OCI IAM policy
oci iam policy create \
  --compartment-id "$COMPARTMENT_OCID" \
  --name "app-compute-policy" \
  --description "Allow app team to manage compute in prod" \
  --statements '["allow group app-team to manage instances in compartment prod","allow group app-team to use volumes in compartment prod"]'
```

### Step 5: Network Topology Translation

Translate an AWS VPC with public/private subnets into an OCI VCN:

```bash
# Export AWS VPC configuration
aws ec2 describe-vpcs --vpc-ids vpc-0123456789abcdef0 --output json > aws-vpc.json
aws ec2 describe-subnets --filters "Name=vpc-id,Values=vpc-0123456789abcdef0" --output json > aws-subnets.json
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-0123456789abcdef0" --output json > aws-routes.json

# Create equivalent OCI VCN
oci network vcn create \
  --compartment-id "$COMPARTMENT_OCID" \
  --display-name "migrated-vcn" \
  --cidr-blocks '["10.0.0.0/16"]' \
  --dns-label "migratedvcn"
```

### Step 6: Data Migration (S3 to Object Storage)

OCI Object Storage supports S3-compatible API, enabling direct migration:

```python
import oci

config = oci.config.from_file("~/.oci/config")
os_client = oci.object_storage.ObjectStorageClient(config)
namespace = os_client.get_namespace().data

# Create destination bucket
os_client.create_bucket(
    namespace_name=namespace,
    create_bucket_details=oci.object_storage.models.CreateBucketDetails(
        compartment_id="COMPARTMENT_OCID",
        name="migrated-data",
        storage_tier="Standard",
    ),
)

# Upload objects (for large migrations, use OCI Data Transfer Service)
with open("data-export.csv", "rb") as f:
    os_client.put_object(
        namespace_name=namespace,
        bucket_name="migrated-data",
        object_name="data-export.csv",
        put_object_body=f,
    )

print(f"Uploaded to: https://objectstorage.{config['region']}.oraclecloud.com/n/{namespace}/b/migrated-data/o/data-export.csv")
```

**S3 Compatibility mode** for tools that speak S3 natively:

```bash
# OCI Object Storage S3-compatible endpoint
# https://<namespace>.compat.objectstorage.<region>.oraclecloud.com

# Use with aws cli (after configuring OCI customer secret keys)
aws s3 sync s3://source-bucket/ s3://migrated-data/ \
  --endpoint-url "https://NAMESPACE.compat.objectstorage.us-ashburn-1.oraclecloud.com"
```

## Output

Successful completion produces:
- AWS-to-OCI and Azure-to-OCI concept mapping tables for architecture translation
- Custom image imported from VMDK into OCI compute (ready to launch instances)
- IAM policies translated from AWS JSON format to OCI policy statements
- Network topology (VCN, subnets, gateways) matching the source VPC/VNet configuration
- Data migrated from S3 to OCI Object Storage via direct upload or S3-compatible API

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthorizedOrNotFound | 404 | Missing IAM policy for image import | Add `allow group migrators to manage custom-images in compartment prod` |
| InvalidParameter | 400 | Unsupported image format | OCI accepts VMDK and QCOW2 only — convert other formats first |
| NotAuthenticated | 401 | API key misconfigured | Re-validate: `oci iam user get --user-id $(grep ^user ~/.oci/config \| cut -d= -f2)` |
| TooManyRequests | 429 | Rate limited during bulk upload | Add delays between Object Storage uploads — no Retry-After header |
| InternalError | 500 | OCI service issue | Retry after 60 seconds; check https://ocistatus.oraclecloud.com |
| Image import stuck in IMPORTING | — | Large image or Object Storage throttling | Check work request: `oci work-requests work-request get --work-request-id <id>` |

## Examples

**Quick migration pre-flight check:**

```bash
# Verify OCI compartment is ready
oci iam compartment get --compartment-id "$COMPARTMENT_OCID" \
  --query 'data.{name:name, state:"lifecycle-state"}' --output table

# Verify Object Storage bucket exists
oci os bucket get --bucket-name migration-staging --namespace "$NAMESPACE" \
  --query 'data.name' --raw-output

# Check image import status
oci compute image list --compartment-id "$COMPARTMENT_OCID" \
  --query 'data[?contains("display-name",`migrated`)].{name:"display-name",state:"lifecycle-state"}' \
  --output table
```

## Resources

- [OCI Migration Guide](https://docs.oracle.com/en-us/iaas/Content/Migration/home.htm) — official migration documentation
- [OCI Compute Custom Images](https://docs.oracle.com/en-us/iaas/Content/Compute/Tasks/imageimportexport.htm) — image import/export procedures
- [OCI S3 Compatibility API](https://docs.oracle.com/en-us/iaas/Content/Object/Tasks/s3compatibleapi.htm) — using S3-compatible tools with OCI
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — ComputeClient, ObjectStorageClient APIs
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — command-line interface documentation
- [OCI Terraform Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs) — infrastructure as code for migrated workloads

## Next Steps

After migration, review `oraclecloud-reference-architecture` to validate the OCI topology, then run `oraclecloud-prod-checklist` to ensure the migrated environment meets production standards.
