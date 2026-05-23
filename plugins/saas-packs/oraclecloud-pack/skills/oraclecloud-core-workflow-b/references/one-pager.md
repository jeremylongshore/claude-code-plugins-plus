# oraclecloud-core-workflow-b — One-Pager

Build OCI networking from scratch — VCN, subnets, gateways, and security rules.

## The Problem

OCI networking (VCN, subnets, security lists, NSGs, gateways) has more moving parts than AWS VPC. A misconfigured security list silently drops traffic with no error — just timeouts. This builds a working network from scratch.

## The Solution

This skill creates a complete OCI network topology step by step: VCN with DNS, internet and NAT gateways, separate route tables for public and private traffic, Network Security Groups with SSH/HTTP/HTTPS rules, and properly configured subnets. It emphasizes NSGs over security lists (the OCI-recommended approach) and includes debugging guidance for silent traffic drops.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and cloud architects building OCI network infrastructure |
| **What** | Complete VCN setup with dual subnets, gateways, route tables, and NSG security rules |
| **When** | Starting a new OCI project, migrating from AWS VPC, or debugging connectivity timeouts caused by missing security rules |

## Key Features

1. **NSG-first security** — Uses Network Security Groups (per-VNIC) instead of security lists (per-subnet) for fine-grained control
2. **Silent drop debugging** — Explains the OCI-specific gotcha where misconfigured rules cause timeouts with no error
3. **Dual-subnet pattern** — Public subnet with internet gateway, private subnet with NAT gateway for outbound-only access

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
