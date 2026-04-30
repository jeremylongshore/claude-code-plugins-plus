---
name: oraclecloud-core-workflow-b
description: "Build OCI networking from scratch \u2014 VCN, subnets, gateways, and\
  \ security rules.\nUse when creating a new VCN, debugging connectivity issues, or\
  \ setting up security lists and NSGs.\nTrigger with \"oci networking\", \"vcn setup\"\
  , \"security list\", \"nsg rules\", \"oci subnet\".\n"
allowed-tools: Read, Write, Edit, Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- oraclecloud
- oci
compatibility: Designed for Claude Code
---
# OCI Networking — VCN, Subnets & Security Rules

## Overview

Build a working OCI network from scratch using the Python SDK. OCI networking (VCN, subnets, security lists, NSGs, gateways) has more moving parts than AWS VPC. A misconfigured security list silently drops traffic with no error — just timeouts. This skill creates a complete network topology with public and private subnets, internet and NAT gateways, route tables, and Network Security Groups (NSGs).

**Purpose:** Build a production-ready VCN with proper routing and security rules that actually works on first deploy.

## Prerequisites

- **OCI Python SDK** — `pip install oci`
- **Config file** at `~/.oci/config` with fields: `user`, `fingerprint`, `tenancy`, `region`, `key_file`
- **IAM policy** — `Allow group Developers to manage virtual-network-family in compartment <name>`
- **Python 3.8+**

## Instructions

### Step 1: Create the VCN

```python
import oci

config = oci.config.from_file("~/.oci/config")
network = oci.core.VirtualNetworkClient(config)

vcn = network.create_vcn(
    oci.core.models.CreateVcnDetails(
        compartment_id=config["tenancy"],
        display_name="app-vcn",
        cidr_blocks=["10.0.0.0/16"],
        dns_label="appvcn",
    )
).data
print(f"VCN created: {vcn.id}")
```

### Step 2: Create Internet Gateway and NAT Gateway

The internet gateway handles inbound/outbound traffic for public subnets. The NAT gateway gives private subnets outbound-only internet access.

```python
# Internet Gateway (for public subnets)
igw = network.create_internet_gateway(
    oci.core.models.CreateInternetGatewayDetails(
        compartment_id=config["tenancy"],
        vcn_id=vcn.id,
        display_name="app-igw",
        is_enabled=True,
    )
).data

# NAT Gateway (for private subnets — outbound only)
nat = network.create_nat_gateway(
    oci.core.models.CreateNatGatewayDetails(
        compartment_id=config["tenancy"],
        vcn_id=vcn.id,
        display_name="app-nat",
    )
).data
print(f"IGW: {igw.id}\nNAT: {nat.id}")
```

### Step 3: Create Route Tables

```python
# Public route table — all traffic via internet gateway
public_rt = network.create_route_table(
    oci.core.models.CreateRouteTableDetails(
        compartment_id=config["tenancy"],
        vcn_id=vcn.id,
        display_name="public-rt",
        route_rules=[
            oci.core.models.RouteRule(
                network_entity_id=igw.id,
                destination="0.0.0.0/0",
                destination_type="CIDR_BLOCK",
            )
        ],
    )
).data

# Private route table — all traffic via NAT gateway
private_rt = network.create_route_table(
    oci.core.models.CreateRouteTableDetails(
        compartment_id=config["tenancy"],
        vcn_id=vcn.id,
        display_name="private-rt",
        route_rules=[
            oci.core.models.RouteRule(
                network_entity_id=nat.id,
                destination="0.0.0.0/0",
                destination_type="CIDR_BLOCK",
            )
        ],
    )
).data
```

### Step 4: Create Network Security Group (NSG)

**Use NSGs instead of security lists.** NSGs attach to VNICs (per-instance) while security lists apply to entire subnets. NSGs are easier to manage and the OCI-recommended approach.

```python
nsg = network.create_network_security_group(
    oci.core.models.CreateNetworkSecurityGroupDetails(
        compartment_id=config["tenancy"],
        vcn_id=vcn.id,
        display_name="app-nsg",
    )
).data

# Add ingress rules — SSH, HTTP, HTTPS
rules = [
    oci.core.models.AddSecurityRuleDetails(
        direction="INGRESS",
        protocol="6",  # TCP
        source="0.0.0.0/0",
        source_type="CIDR_BLOCK",
        tcp_options=oci.core.models.TcpOptions(
            destination_port_range=oci.core.models.PortRange(min=port, max=port)
        ),
        description=desc,
    )
    for port, desc in [(22, "SSH"), (80, "HTTP"), (443, "HTTPS")]
]

# Add egress rule — allow all outbound
rules.append(
    oci.core.models.AddSecurityRuleDetails(
        direction="EGRESS",
        protocol="all",
        destination="0.0.0.0/0",
        destination_type="CIDR_BLOCK",
        description="Allow all outbound",
    )
)

network.add_network_security_group_security_rules(
    network_security_group_id=nsg.id,
    add_network_security_group_security_rules_details=oci.core.models.AddNetworkSecurityGroupSecurityRulesDetails(
        security_rules=rules
    ),
)
print(f"NSG created with {len(rules)} rules: {nsg.id}")
```

### Step 5: Create Public and Private Subnets

```python
identity = oci.identity.IdentityClient(config)
ad = identity.list_availability_domains(compartment_id=config["tenancy"]).data[0].name

# Public subnet
public_subnet = network.create_subnet(
    oci.core.models.CreateSubnetDetails(
        compartment_id=config["tenancy"],
        vcn_id=vcn.id,
        display_name="public-subnet",
        cidr_block="10.0.1.0/24",
        route_table_id=public_rt.id,
        dns_label="pubsub",
        prohibit_public_ip_on_vnic=False,  # Allow public IPs
    )
).data

# Private subnet
private_subnet = network.create_subnet(
    oci.core.models.CreateSubnetDetails(
        compartment_id=config["tenancy"],
        vcn_id=vcn.id,
        display_name="private-subnet",
        cidr_block="10.0.2.0/24",
        route_table_id=private_rt.id,
        dns_label="privsub",
        prohibit_public_ip_on_vnic=True,  # No public IPs
    )
).data

print(f"Public subnet: {public_subnet.id}")
print(f"Private subnet: {private_subnet.id}")
```

### Step 6: Verify Connectivity

```python
# List all subnets in the VCN to confirm setup
subnets = network.list_subnets(
    compartment_id=config["tenancy"],
    vcn_id=vcn.id
).data

for s in subnets:
    print(f"{s.display_name} | {s.cidr_block} | Public IPs: {not s.prohibit_public_ip_on_vnic}")
```

## Output

Successful completion produces:
- A VCN with a /16 CIDR block and DNS resolution enabled
- Internet gateway (public traffic) and NAT gateway (private outbound)
- Separate route tables for public and private subnets
- An NSG with SSH (22), HTTP (80), and HTTPS (443) ingress rules
- Public and private subnets with correct routing

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Not authorized | 404 NotAuthorizedOrNotFound | Missing IAM policy for virtual-network-family | Add policy: `Allow group X to manage virtual-network-family in compartment Y` |
| CIDR overlap | 400 InvalidParameter | Subnet CIDR conflicts with existing subnet | Use non-overlapping /24 blocks within the VCN /16 range |
| Limit exceeded | 400 LimitExceeded | VCN or subnet limit reached | Check limits in Console > Governance > Limits; request increase |
| Silent traffic drop | N/A | Security list or NSG missing ingress rule | Check NSG rules — OCI drops unmatched traffic with no ICMP unreachable |
| Not authenticated | 401 NotAuthenticated | Bad API key or config | Verify `~/.oci/config` key_file and fingerprint |
| Rate limited | 429 TooManyRequests | Too many API calls | Add backoff; OCI does not return Retry-After header |

**Debugging silent drops:** If traffic times out, check in this order: (1) NSG ingress rules, (2) security list rules, (3) route table entries, (4) gateway exists and is enabled. OCI applies security lists AND NSGs — traffic must pass both.

## Examples

**Quick VCN list via CLI:**

```bash
oci network vcn list \
  --compartment-id <OCID> \
  --query "data[*].{Name:\"display-name\",CIDR:\"cidr-blocks\"}" \
  --output table
```

**Check NSG rules for debugging:**

```python
rules = network.list_network_security_group_security_rules(
    network_security_group_id=nsg.id
).data
for r in rules:
    print(f"{r.direction} | {r.protocol} | {r.source or r.destination} | {r.description}")
```

## Resources

- [VCN Overview](https://docs.oracle.com/en-us/iaas/Content/) — networking concepts and best practices
- [Python SDK Reference](https://docs.oracle.com/en-us/iaas/tools/python/latest/) — VirtualNetworkClient API
- [CLI Reference](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) — `oci network` commands
- [Terraform OCI Provider](https://registry.terraform.io/providers/oracle/oci/latest/docs) — infrastructure as code
- [Known Issues](https://docs.oracle.com/en-us/iaas/Content/knownissues.htm) — current networking issues

## Next Steps

After networking is in place, launch instances with `oraclecloud-core-workflow-a` (use the subnet IDs from Step 5), or set up monitoring with `oraclecloud-query-transform` to watch network traffic metrics.
