# oraclecloud-migration-deep-dive — One-Pager

Migrate workloads from AWS or Azure to OCI — IAM translation, networking mapping, compute image import, and data migration.

## The Problem

Migrating to OCI from AWS or Azure requires translating IAM concepts (roles to policies, accounts to compartments), networking (VPC to VCN, Security Groups to NSGs), and compute (AMI to custom image). OCI's migration tools are underdocumented compared to AWS Migration Hub or Azure Migrate. Teams waste weeks discovering that OCI subnets are regional (not AZ-scoped), that IAM policies use a completely different syntax, and that image imports only accept VMDK and QCOW2.

## The Solution

Comprehensive concept mapping tables (AWS-to-OCI and Azure-to-OCI) covering IAM, networking, compute, storage, and monitoring. Step-by-step custom image import from VMDK via Object Storage. IAM policy translation from AWS JSON to OCI human-readable statements. Network topology translation from VPC/VNet to VCN. Data migration via direct upload or S3-compatible API.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Cloud architects, platform engineers, and migration teams moving from AWS or Azure to OCI |
| **What** | Concept mapping tables, image import procedures, IAM translation, network topology, and data migration |
| **When** | Planning a cloud migration, executing a lift-and-shift, or training teams on OCI equivalents |

## Key Features

1. **Dual mapping tables** — AWS-to-OCI and Azure-to-OCI covering 15+ service equivalents each
2. **Custom image import** — VMDK export from AWS, Object Storage staging, OCI image creation
3. **IAM policy translation** — AWS JSON policies converted to OCI human-readable statements
4. **S3-compatible data migration** — use existing S3 tools to move data to OCI Object Storage

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
