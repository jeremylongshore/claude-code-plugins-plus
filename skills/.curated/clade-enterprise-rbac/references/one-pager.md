# clade-enterprise-rbac — One-Pager

Manage Anthropic workspaces, API keys, spending limits, and team access for enterprise deployments.

## The Problem

Teams scaling Claude usage beyond a single developer quickly run into access control problems: shared API keys with no blast radius isolation, no spending caps to prevent runaway costs, no separation between dev and prod environments, and no offboarding process when team members leave.

## The Solution

This skill maps out Anthropic's Organization/Workspace model and provides a concrete checklist for enterprise-grade access control: separate workspaces per environment, dedicated API keys per service, spending limits, a 90-day key rotation schedule, and audit log reviews.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Engineering managers, platform teams, and DevOps engineers managing Claude access across a team or organization |
| **What** | Workspace structure design, API key naming/rotation policy, spending limits, and an access control checklist |
| **When** | When scaling from a single developer to a team, setting up production environments, or conducting a security review of Claude access |

## Key Features

1. **Organization/Workspace Model** — Visual diagram showing how to structure workspaces for production, staging, and development with scoped API keys
2. **API Key Best Practices** — One key per service/environment, descriptive naming (`prod-recommendation-service`), quarterly rotation, and blast radius isolation
3. **Access Control Checklist** — Six-item checklist covering workspace separation, spending alerts, key rotation, offboarding, and audit log review

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
