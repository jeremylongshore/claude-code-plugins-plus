# navan-enterprise-rbac — One-Pager

Configure Navan's admin roles, travel policies, approval workflows, and department-level access controls.

## The Problem

Enterprise Navan deployments manage hundreds or thousands of travelers across multiple departments, cost centers, and approval hierarchies. Without proper RBAC configuration, travel policies are inconsistently enforced — employees book out-of-policy flights, expense approvals bypass managers, and admin access is either too broad (everyone is an admin) or too narrow (bottlenecked on a single admin). Navan's policy engine is powerful but underdocumented for API-driven configuration.

## The Solution

This skill maps Navan's admin role hierarchy, configures travel policy rules (in-policy vs out-of-policy enforcement), sets up multi-tier approval workflows, and implements department-level access scoping. It covers both the admin UI configuration and the API-driven policy management for programmatic control at scale.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Travel managers, IT admins, and developers building policy-enforcement automation for Navan |
| **What** | Role hierarchy setup, travel policy rules, approval chain configuration, department-scoped access controls |
| **When** | Enterprise Navan rollout, adding new departments, tightening travel policy compliance, or building custom approval workflows |

## Key Features

1. **Role hierarchy mapping** — Full breakdown of Navan's admin roles from Global Admin to Traveler with permission boundaries
2. **Policy rule engine** — In-policy vs out-of-policy booking enforcement with configurable thresholds and exceptions
3. **Approval workflows** — Multi-tier approval chains with manager escalation, department routing, and auto-approval rules

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
