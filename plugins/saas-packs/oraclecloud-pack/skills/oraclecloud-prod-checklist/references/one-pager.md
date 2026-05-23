# oraclecloud-prod-checklist — One-Pager

Pre-production readiness checklist for OCI — backup policies, security audit, key rotation, encryption, and Cloud Guard.

## The Problem

OCI has no "Well-Architected Review" like AWS. There is no built-in tool that tells you whether your OCI environment is production-ready. Teams go live with Oracle-managed encryption (not compliant), no backup policies, 0.0.0.0/0 security list rules, API keys older than a year, and no Cloud Guard — then find out during the first audit or outage.

## The Solution

An 8-point pass/fail checklist that verifies compartment isolation, backup policies, security list rules, API key age, boot volume encryption (customer-managed keys), OS Management agent status, Cloud Guard detector recipes, and vulnerability scanning. Every check runs via OCI CLI or Python SDK with concrete pass/fail criteria and remediation commands.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Platform engineers, security teams, and compliance auditors reviewing OCI environments |
| **What** | 8-point production readiness audit covering security, resilience, encryption, and monitoring |
| **When** | Before production launch, during quarterly audits, after infrastructure changes, or for compliance reporting |

## Key Features

1. **Compartment isolation** — verifies prod is not in root tenancy with least-privilege policies
2. **Backup verification** — checks every boot volume has an assigned backup policy
3. **Security rule audit** — flags unrestricted 0.0.0.0/0 ingress beyond ports 80/443
4. **Key rotation enforcement** — identifies API keys older than 90 days

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
