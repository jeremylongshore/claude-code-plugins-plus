# oraclecloud-schema-migration — One-Pager

Migrate to OCI Autonomous Database — wallet setup, mTLS, Data Pump, and python-oracledb.

## The Problem

Autonomous Database is OCI's crown jewel but migrating to it from standard Oracle DB or other databases is full of gotchas — wallet downloads, mTLS requirements, SQL Developer Web vs traditional tools, Data Pump incompatibilities.

## The Solution

This skill provides the complete migration workflow: provision an Autonomous Database (including Always Free tier), download and extract the mTLS wallet via SDK, connect using python-oracledb in thin mode (no Oracle Client needed), export data with ADB-compatible Data Pump parameters, import via Object Storage and DBMS_CLOUD, and verify migration with table counts and invalid object detection.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | DBAs and backend developers migrating to or connecting with OCI Autonomous Database |
| **What** | ADB provisioning, wallet download, python-oracledb connection, Data Pump export/import with ADB exclusions |
| **When** | Migrating an existing Oracle or other database to ADB, setting up a new ADB instance, or troubleshooting mTLS wallet connection issues |

## Key Features

1. **Wallet workflow** — SDK-based download, extraction, and configuration for mTLS connections
2. **ADB-safe Data Pump** — Export with correct `exclude=` list to avoid import failures on unsupported object types
3. **Thin mode connection** — python-oracledb connects directly with wallet files, no Oracle Client installation needed

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
