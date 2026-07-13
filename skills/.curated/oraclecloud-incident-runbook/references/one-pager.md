# oraclecloud-incident-runbook — One-Pager

Self-service incident runbook for OCI outages — health probes, instance recovery, cross-AD/region failover.

## The Problem

OCI status page doesn't acknowledge outages in real time. Support is slow (4+ hours for Sev-1). When your instances go down (like London Jan 2026 — 502s, instances disappearing for 10 minutes), you need a self-service runbook: independent health probes, automated instance recovery, and cross-region failover. Waiting for Oracle to acknowledge the problem costs you downtime.

## The Solution

This runbook provides independent API health probes (Identity, Compute, Networking), automated severity classification (P1/P2/P3), instance recovery actions (reset, reboot, stop/start), cross-AD failover from boot volume backups, and cross-region failover for total region outages. Every step runs via OCI CLI or Python SDK — no console needed.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | SREs, platform engineers, and on-call teams managing OCI workloads |
| **What** | Executable incident runbook with health probes, recovery actions, and multi-AD/region failover |
| **When** | Instance outage, API degradation, status page contradicts reality, or proactive DR testing |

## Key Features

1. **Independent health probes** — detect degradation before the OCI status page acknowledges it
2. **Automated instance recovery** — reset, reboot, or stop/start with a single CLI command
3. **Cross-AD failover** — launch replacement instances from boot volume backups in alternate ADs
4. **Cross-region DR** — pre-replicated boot volumes enable region-level failover

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
