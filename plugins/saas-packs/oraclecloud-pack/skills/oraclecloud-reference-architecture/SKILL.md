---
name: oraclecloud-reference-architecture
description: 'Standard 3-tier OCI reference architecture with VCN, subnets, gateways,
  load balancer, compute, and Autonomous DB.

  Use when designing a new OCI deployment, translating AWS/Azure patterns, or creating
  Terraform for OCI infrastructure.

  Trigger with "oraclecloud architecture", "oci reference design", "oci 3 tier", "oci
  vpc design".

  '
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
# Oracle Cloud Reference Architecture

## Overview

OCI architecture has more moving parts than AWS or Azure. Where AWS has VPC + subnets + internet gateway, OCI has VCN + regional subnets + Internet Gateway + NAT Gateway + Service Gateway + DRG (Dynamic Routing Gateway) + LPG (Local Peering Gateway) — and getting the routing tables wrong means silent packet drops with no error. This provides the standard 3-tier architecture (web/app/db) with every OCI-specific component wired correctly, plus Terraform code to deploy it.

**Purpose:** Produce a production-ready 3-tier OCI architecture with correctly configured networking, gateways, security rules, and compute/database tiers — deployable via Terraform.

## Prerequisites

- **OCI account** with an active tenancy — https://cloud.oracle.com
- **OCI CLI installed and configured** — `~/.oci/config` validated (see `oraclecloud-install-auth`)
- **Python 3.8+** with the OCI SDK — `pip install oci`
- **Terraform 1.5+** with the OCI provider — https://registry.terraform.io/providers/oracle/oci/latest/docs
- **Compartment OCID** for the target environment
- Familiarity with CIDR notation for subnet planning

## Instructions

### Step 1: Architecture Overview

```
┌─────────────────────────── OCI Region (us-ashburn-1) ───────────────────────────┐
│                                                                                  │
│  ┌────────────────────────── VCN (10.0.0.0/16) ──────────────────────────────┐  │
│  │                                                                            │  │
│  │  ┌─── Internet GW ───┐  ┌─── NAT GW ───┐  ┌─── Service GW ───┐         │  │
│  │  └────────┬───────────┘  └──────┬────────┘  └───────┬──────────┘         │  │
│  │           │                      │                    │                    │  │
│  │  ┌────────▼──────────────────────────────────────────────────────────┐    │  │
│  │  │ Public Subnet (10.0.1.0/24) — Web Tier                           │    │  │
│  │  │   Load Balancer (public) → routes to App Tier                    │    │  │
│  │  │   Bastion Host (optional)                                        │    │  │
│  │  └──────────────────────┬───────────────────────────────────────────┘    │  │
│  │                          │                                                │  │
│  │  ┌──────────────────────▼───────────────────────────────────────────┐    │  │
│  │  │ Private Subnet (10.0.2.0/24) — App Tier                         │    │  │
│  │  │   Compute Instances (VM.Standard.E4.Flex)                        │    │  │
│  │  │   → NAT GW for outbound internet (patching, APIs)               │    │  │
│  │  │   → Service GW for OCI services (Object Storage, etc.)          │    │  │
│  │  └──────────────────────┬───────────────────────────────────────────┘    │  │
│  │                          │                                                │  │
│  │  ┌──────────────────────▼───────────────────────────────────────────┐    │  │
│  │  │ Private Subnet (10.0.3.0/24) — DB Tier                          │    │  │
│  │  │   Autonomous Database (ATP or ADW)                               │    │  │
│  │  │   → Service GW only (no internet access)                         │    │  │
│  │  └──────────────────────────────────────────────────────────────────┘    │  │
│  │                                                                            │  │
│  │  ┌─── DRG ───┐  ← On-premises or cross-region peering                   │  │
│  │  └────────────┘                                                           │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### Step 2: Gateway Types Explained

| Gateway | Purpose | Attached To | Use Case |
|---------|---------|-------------|----------|
| **Internet Gateway** | Bidirectional internet access | Public subnet route table | Load balancers, bastion hosts |
| **NAT Gateway** | Outbound-only internet access | Private subnet route table | App servers needing patches, external APIs |
| **Service Gateway** | Access OCI services without internet | Private subnet route table | Object Storage, Autonomous DB, OCI APIs |
| **DRG (Dynamic Routing Gateway)** | On-premises / cross-region connectivity | VCN attachment | VPN, FastConnect, inter-region peering |
| **LPG (Local Peering Gateway)** | VCN-to-VCN within same region | VCN attachment | Shared services VCN, hub-spoke topology |

### Step 3: Create the VCN and Subnets (Python SDK)

```python
import oci

config = oci.config.from_file("~/.oci/config")
network = oci.core.VirtualNetworkClient(config)

# Create VCN
vcn = network.create_vcn(
    oci.core.models.CreateVcnDetails(
        compartment_id="COMPARTMENT_OCID",
        display_name="prod-vcn",
        cidr_blocks=["10.0.0.0/16"],
        dns_label="prodvcn",
    )
).data
print(f"VCN created: {vcn.id}")

# Create public subnet (web tier)
web_subnet = network.create_subnet(
    oci.core.models.CreateSubnetDetails(
        compartment_id="COMPARTMENT_OCID",
        vcn_id=vcn.id,
        display_name="web-subnet-public",
        cidr_block="10.0.1.0/24",
        dns_label="web",
        prohibit_internet_ingress=False,  # Public subnet
    )
).data

# Create private subnet (app tier)
app_subnet = network.create_subnet(
    oci.core.models.CreateSubnetDetails(
        compartment_id="COMPARTMENT_OCID",
        vcn_id=vcn.id,
        display_name="app-subnet-private",
        cidr_block="10.0.2.0/24",
        dns_label="app",
        prohibit_internet_ingress=True,  # Private subnet
    )
).data

# Create private subnet (db tier)
db_subnet = network.create_subnet(
    oci.core.models.CreateSubnetDetails(
        compartment_id="COMPARTMENT_OCID",
        vcn_id=vcn.id,
        display_name="db-subnet-private",
        cidr_block="10.0.3.0/24",
        dns_label="db",
        prohibit_internet_ingress=True,  # Private subnet
    )
).data

print(f"Subnets: web={web_subnet.id}, app={app_subnet.id}, db={db_subnet.id}")
```

### Step 4: Create Gateways and Route Tables

```python
# Internet Gateway (for web tier)
igw = network.create_internet_gateway(
    oci.core.models.CreateInternetGatewayDetails(
        compartment_id="COMPARTMENT_OCID",
        vcn_id=vcn.id,
        display_name="prod-igw",
        is_enabled=True,
    )
).data

# NAT Gateway (for app tier outbound)
nat = network.create_nat_gateway(
    oci.core.models.CreateNatGatewayDetails(
        compartment_id="COMPARTMENT_OCID",
        vcn_id=vcn.id,
        display_name="prod-nat",
    )
).data

# Service Gateway (for db tier → OCI services)
services = network.list_services().data
all_services = next(s for s in services if "All" in s.name)
sgw = network.create_service_gateway(
    oci.core.models.CreateServiceGatewayDetails(
        compartment_id="COMPARTMENT_OCID",
        vcn_id=vcn.id,
        display_name="prod-sgw",
        services=[oci.core.models.ServiceIdRequestDetails(service_id=all_services.id)],
    )
).data

print(f"Gateways: igw={igw.id}, nat={nat.id}, sgw={sgw.id}")
```

### Step 5: Terraform Deployment

```hcl
# provider.tf
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

provider "oci" {
  config_file_profile = "DEFAULT"
}

# vcn.tf
resource "oci_core_vcn" "prod" {
  compartment_id = var.compartment_id
  display_name   = "prod-vcn"
  cidr_blocks    = ["10.0.0.0/16"]
  dns_label      = "prodvcn"
}

resource "oci_core_internet_gateway" "prod" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.prod.id
  display_name   = "prod-igw"
  enabled        = true
}

resource "oci_core_nat_gateway" "prod" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.prod.id
  display_name   = "prod-nat"
}

resource "oci_core_subnet" "web" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.prod.id
  display_name               = "web-subnet-public"
  cidr_block                 = "10.0.1.0/24"
  dns_label                  = "web"
  prohibit_internet_ingress  = false
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.web.id]
}

resource "oci_core_subnet" "app" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.prod.id
  display_name               = "app-subnet-private"
  cidr_block                 = "10.0.2.0/24"
  dns_label                  = "app"
  prohibit_internet_ingress  = true
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.app.id]
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.prod.id
  display_name   = "public-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.prod.id
  }
}

resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.prod.id
  display_name   = "private-rt"
  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_nat_gateway.prod.id
  }
}
```

### Step 6: Component Mapping (AWS/Azure → OCI)

| Concept | AWS | Azure | OCI |
|---------|-----|-------|-----|
| Virtual network | VPC | VNet | VCN |
| Subnet | Subnet (AZ-scoped) | Subnet | Subnet (regional) |
| Internet access | Internet Gateway | — (default) | Internet Gateway |
| Outbound only | NAT Gateway | NAT Gateway | NAT Gateway |
| Private service access | VPC Endpoint | Private Endpoint | Service Gateway |
| Cross-network peering | VPC Peering | VNet Peering | LPG / DRG |
| Firewall rules | Security Group | NSG | NSG + Security List |
| Load balancer | ALB/NLB | Azure LB | OCI Load Balancer |
| Managed database | RDS/Aurora | Azure SQL | Autonomous Database |

## Output

Successful completion produces:
- A 3-tier VCN architecture with public (web), private (app), and private (db) subnets
- Internet Gateway, NAT Gateway, and Service Gateway correctly routed to their respective subnets
- Route tables with proper rules (public → IGW, private → NAT/SGW)
- Terraform code deployable with `terraform plan && terraform apply`
- Component mapping table for teams coming from AWS or Azure

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| NotAuthorizedOrNotFound | 404 | Missing IAM policy for VCN creation | Add `allow group netadmins to manage virtual-network-family in compartment prod` |
| InvalidParameter | 400 | Overlapping CIDR blocks | Ensure VCN CIDR does not overlap with existing VCNs or on-premises networks |
| LimitExceeded | 400 | Hit VCN or subnet service limit | Request limit increase via Console > Governance > Service Limits |
| TooManyRequests | 429 | Rate limited during bulk creation | Add 2-second delays between resource creation calls |
| InternalError | 500 | OCI service issue during provisioning | Retry after 60 seconds; check https://ocistatus.oraclecloud.com |
| Terraform provider crash | — | OCI provider version incompatibility | Pin provider: `version = "~> 5.0"` (see `oraclecloud-upgrade-migration`) |

## Examples

**Quick VCN validation (CLI):**

```bash
# List VCNs in a compartment
oci network vcn list \
  --compartment-id "$COMPARTMENT_OCID" \
  --query 'data[].{name:"display-name", cidr:"cidr-blocks", state:"lifecycle-state"}' \
  --output table

# List subnets in a VCN
oci network subnet list \
  --compartment-id "$COMPARTMENT_OCID" \
  --vcn-id "$VCN_OCID" \
  --query 'data[].{name:"display-name", cidr:"cidr-block", public:"prohibit-internet-ingress"}' \
  --output table
```

**Validate route table connectivity:**

```bash
# Verify public subnet routes to Internet Gateway
oci network route-table get --rt-id "$PUBLIC_RT_OCID" \
  --query 'data."route-rules"[].{dest:destination, target:"network-entity-id"}' \
  --output table
```

## Resources

- [OCI Networking Overview](https://docs.oracle.com/en-us/iaas/Content/Network/Concepts/overview.htm) — VCN, subnets, gateways, and route tables
- [OCI Terraform Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs) — infrastructure as code for OCI
- [OCI Reference Architectures](https://docs.oracle.com/solutions/) — Oracle-published architecture patterns
- [OCI Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — VirtualNetworkClient API
- [OCI CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — network commands
- [OCI Pricing](https://www.oracle.com/cloud/pricing/) — VCN and gateway pricing (VCN, IGW, and LPG are free)

## Next Steps

After deploying the architecture, run `oraclecloud-prod-checklist` to validate production readiness, or see `oraclecloud-migration-deep-dive` for translating existing AWS/Azure workloads into this architecture pattern.
