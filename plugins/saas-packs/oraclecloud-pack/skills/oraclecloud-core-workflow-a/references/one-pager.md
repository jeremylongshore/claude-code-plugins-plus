# oraclecloud-core-workflow-a — One-Pager

Launch, manage, and scale OCI compute instances with capacity retry logic.

## The Problem

Compute is the entry point but "out of capacity" errors, shape selection confusion (Flex vs Standard, AMD vs ARM vs Intel), and boot volume management make it harder than AWS EC2. This covers launch, manage, and scale with capacity retry built in.

## The Solution

This skill provides a complete compute workflow: shape comparison to pick the right instance type, launch with automatic retry across availability domains when capacity is unavailable, instance lifecycle management (stop/start/reboot/terminate), and VNIC-based IP address discovery.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DevOps engineers and developers provisioning OCI compute infrastructure |
| **What** | Instance launch with AD capacity retry, shape selection guide, lifecycle actions, metadata and IP retrieval |
| **When** | Provisioning new workloads, handling capacity errors, managing instance lifecycle, or migrating from AWS EC2 |

## Key Features

1. **Shape comparison table** — Flex shapes (A1 ARM, E5 AMD, Standard3 Intel) with OCPU ranges and use cases
2. **Capacity retry pattern** — Automatically retries launch across all availability domains on "Out of host capacity" errors
3. **Full lifecycle management** — SOFTSTOP, START, SOFTRESET, terminate with boot volume preservation

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
