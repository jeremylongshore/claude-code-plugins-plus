# oraclecloud-performance-tuning — One-Pager

Map OCI compute shapes, block volume tiers, and network bandwidth to your workload requirements.

## The Problem

OCI shape naming is opaque (VM.Standard.E5.Flex vs VM.Standard3.Flex vs VM.Standard.A1.Flex), block volume performance tiers (Balanced/Higher/Ultra High) have different IOPS/throughput, and network bandwidth is shape-dependent. Teams waste money on over-provisioned infrastructure or suffer performance problems from under-provisioned storage because the performance characteristics aren't obvious from the names.

## The Solution

This skill maps performance to shapes with comparison tables, explains block volume VPUs/GB tiers with concrete IOPS and throughput numbers, and provides Python SDK code to query available shapes, create performance-tuned volumes, and monitor actual IOPS and network bandwidth against expected limits.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and architects sizing OCI infrastructure for production workloads |
| **What** | Shape performance comparison, block volume tier selection, performance monitoring queries, and right-sizing analysis |
| **When** | Provisioning new infrastructure, troubleshooting performance issues, or right-sizing existing instances |

## Key Features

1. **Shape comparison table** — Processor, OCPU range, and network bandwidth for all major flex shapes
2. **Block volume tiers** — IOPS and throughput by tier with `vpus_per_gb` configuration values
3. **Performance monitoring** — SDK queries for CPU, disk IOPS, and network bandwidth validation

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
