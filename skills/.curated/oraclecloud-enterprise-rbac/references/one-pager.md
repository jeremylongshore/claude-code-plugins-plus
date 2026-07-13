# oraclecloud-enterprise-rbac — One-Pager

Design OCI compartment hierarchies, dynamic groups, and cross-tenancy access patterns.

## The Problem

OCI compartments are powerful but the inheritance model is confusing — policies at root vs compartment level behave differently, dynamic groups for compute-to-service auth require matching rules that take minutes to propagate, and cross-tenancy access patterns need matching policies on both sides. Most teams get this wrong and over-permission everything with `manage all-resources in tenancy`.

## The Solution

This skill designs a proper enterprise compartment hierarchy (shared-infra, security, dev, staging, prod with nested compute/data compartments), explains the three critical policy inheritance rules, sets up dynamic groups for Instance Principal authentication (no API keys on instances), and implements tag-based access control for fine-grained cross-compartment permissions.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Cloud architects and security teams designing OCI organization structure for enterprise deployments |
| **What** | Compartment hierarchy, least-privilege IAM policies, dynamic groups for Instance Principal, and tag-based access control |
| **When** | Setting up a new OCI tenancy, migrating from flat compartment structure, auditing over-permissioned policies, or enabling keyless auth for compute instances |

## Key Features

1. **Compartment hierarchy design** — Standard enterprise layout with environment separation and nested compute/data compartments
2. **Dynamic groups and Instance Principal** — Keyless authentication for OCI instances and functions using matching rules
3. **Tag-based access control** — Fine-grained permissions using defined tags instead of compartment-only scoping

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
