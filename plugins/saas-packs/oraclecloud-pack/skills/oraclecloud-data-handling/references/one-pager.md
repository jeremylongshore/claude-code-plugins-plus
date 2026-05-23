# oraclecloud-data-handling — One-Pager

Manage OCI Object Storage — buckets, uploads, PARs, and lifecycle policies.

## The Problem

Object Storage PAR (Pre-Authenticated Request) URLs expire silently. Multipart uploads over 50GB require manual part management. Lifecycle policies can delete data unexpectedly. This covers the safe patterns.

## The Solution

This skill provides safe Object Storage operations: namespace discovery, bucket creation with versioning, simple and multipart uploads via UploadManager, PAR creation with explicit expiry and audit/revocation workflows, and lifecycle policies with clear warnings about auto-deletion risks.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers and data engineers storing files, sharing data via signed URLs, or managing storage lifecycle |
| **What** | Bucket ops, object upload/download, PAR management with expiry tracking, lifecycle policy configuration |
| **When** | Setting up data storage, sharing files with external partners via PAR, or automating storage cost management with lifecycle rules |

## Key Features

1. **PAR expiry safety** — Explains the silent 404 gotcha and provides audit/revocation patterns
2. **Automatic multipart** — Uses UploadManager to handle chunking for files over 50MB transparently
3. **Lifecycle guardrails** — Warnings about auto-deletion with safe archive-first patterns

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
