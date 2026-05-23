# oraclecloud-hello-world — One-Pager

Launch your first OCI compute instance with capacity retry logic for Always Free ARM shapes.

## The Problem

Your first OCI compute instance fails with "Out of host capacity" — especially on Always Free ARM shapes (VM.Standard.A1.Flex). This error means the data center literally has no available hosts; it is not a permissions issue. Retry automation exists (4+ GitHub repos dedicated to it), but new users do not know it exists and assume their account is broken. Beyond capacity, first-time users also struggle with the OCID soup: image OCIDs, subnet OCIDs, and availability domain names that differ per region.

## The Solution

This skill gets you a running instance, including the retry loop that makes Always Free ARM shapes actually usable. It covers listing existing instances, discovering available shapes and images, launching with both standard and ARM shapes, waiting for RUNNING state, and full lifecycle operations (stop/start/terminate). Both Python SDK and OCI CLI examples are provided.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers launching their first OCI compute instance or automating instance provisioning |
| **What** | A running compute instance with the capacity retry pattern, lifecycle operations, and public IP retrieval |
| **When** | First OCI project setup, Always Free ARM provisioning, or building instance automation scripts |

## Key Features

1. **Capacity retry loop** — Automated retry with jitter for "Out of host capacity" errors on ARM shapes
2. **Shape and image discovery** — List available shapes and platform images before launching
3. **Full lifecycle** — Launch, wait-for-running, stop, start, reboot, and terminate operations
4. **CLI equivalents** — Every Python operation also shown as an OCI CLI command

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
