# oraclecloud-reference-architecture — One-Pager

Standard 3-tier OCI reference architecture with VCN, subnets, gateways, load balancer, compute, and Autonomous DB.

## The Problem

OCI architecture has more moving parts than AWS or Azure. Where AWS has VPC + subnets + internet gateway, OCI has VCN + regional subnets + Internet Gateway + NAT Gateway + Service Gateway + DRG + LPG — and getting the routing tables wrong means silent packet drops with no error. Teams coming from AWS waste days figuring out which gateways attach where.

## The Solution

This provides the standard 3-tier architecture (web/app/db) with every OCI-specific component wired correctly: public subnet with Internet Gateway for the web tier, private subnets with NAT Gateway and Service Gateway for app and database tiers. Includes a Terraform deployment, an ASCII architecture diagram, and an AWS/Azure-to-OCI concept mapping table.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Cloud architects, infrastructure engineers, and teams migrating to OCI from AWS/Azure |
| **What** | Production-ready 3-tier VCN architecture with Terraform code and gateway routing |
| **When** | Starting a new OCI project, designing network topology, or translating AWS/Azure patterns to OCI |

## Key Features

1. **ASCII architecture diagram** — visual reference for VCN, subnets, and all five gateway types
2. **Python SDK provisioning** — programmatic VCN, subnet, and gateway creation
3. **Terraform deployment** — complete IaC for the 3-tier architecture
4. **Cross-cloud mapping table** — AWS and Azure concept equivalents for every OCI component

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
