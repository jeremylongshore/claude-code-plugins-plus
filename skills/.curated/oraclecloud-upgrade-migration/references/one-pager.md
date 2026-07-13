# oraclecloud-upgrade-migration — One-Pager

Safely upgrade OCI Python SDK and Terraform provider — version pinning, breaking change detection, and rollback.

## The Problem

OCI Terraform provider and Python SDK break backwards compatibility more often than AWS equivalents. Provider crashes on `terraform plan`, deprecated resources removed without migration paths, SDK memory leak fixes that change object lifecycle semantics, and authentication class renames between minor versions. Upgrading without a safety net means discovering breakage in production.

## The Solution

A safe upgrade workflow: audit current versions, check against a known breaking changes table, upgrade with version constraints (not `--latest`), validate all core SDK clients, run `terraform plan` to detect schema drift, scan for deprecated patterns, and roll back cleanly if anything breaks. Backup files are created before every upgrade step.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Platform engineers, DevOps teams, and infrastructure developers maintaining OCI tooling |
| **What** | Safe upgrade workflow for OCI Python SDK, CLI, and Terraform provider with rollback procedures |
| **When** | Scheduled dependency upgrades, after security advisories, before major deployments, or after hitting known bugs |

## Key Features

1. **Known breaking changes table** — documented SDK and Terraform provider issues with mitigations
2. **Version-constrained upgrades** — pin to minor ranges, never unbounded `--latest`
3. **Client validation script** — tests all 6 core SDK clients after upgrade
4. **Rollback procedures** — pip freeze backup, lock file backup, and git-level revert

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
