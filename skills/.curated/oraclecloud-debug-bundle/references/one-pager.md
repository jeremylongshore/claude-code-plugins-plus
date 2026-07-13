# oraclecloud-debug-bundle — One-Pager

Collect OCI instance diagnostics — serial console, cloud-init logs, metadata, and VCN flow logs — into a single debug bundle.

## The Problem

When an OCI instance goes unresponsive ("unavailable due to an issue with the underlying infrastructure"), you need serial console output, cloud-init logs, instance metadata, and VCN flow logs — but the console is the LAST place you want to be debugging. Clicking through the OCI Console to gather each piece takes 15+ minutes, and you still miss VCN flow data. OCI Support will ask for all of this anyway when you open a ticket.

## The Solution

This skill collects every diagnostic artifact via OCI CLI commands into a single timestamped `.tar.gz` bundle. Serial console history captures boot-time failures and kernel panics. Cloud-init logs (retrieved via instance agent) show provisioning errors. VCN flow logs reveal network-level blocks. Instance metrics expose CPU exhaustion. The bundle is ready to attach to a support ticket or analyze locally.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | OCI platform engineers, SREs, and DevOps teams managing compute instances |
| **What** | A CLI-driven diagnostic bundle containing serial console, cloud-init, flow logs, metadata, and metrics |
| **When** | Instance is unresponsive, stuck in provisioning, showing infrastructure errors, or you need evidence for a support ticket |

## Key Features

1. **Serial console capture** — kernel panics and boot failures without SSH access
2. **Cloud-init retrieval** — provisioning logs via the instance agent run-command plugin
3. **VCN flow logs** — network-level traffic data for the last hour
4. **Single archive output** — timestamped `.tar.gz` ready for support tickets or postmortems

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
