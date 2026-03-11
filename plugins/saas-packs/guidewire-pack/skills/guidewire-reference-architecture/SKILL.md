---
name: guidewire-reference-architecture
description: |
  Enterprise reference architecture for Guidewire InsuranceSuite Cloud deployments.
  Use when designing system architecture, planning integrations,
  or understanding Guidewire cloud infrastructure patterns.
  Trigger with phrases like "guidewire architecture", "system design",
  "integration architecture", "enterprise guidewire", "reference architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Reference Architecture

## Overview

Enterprise reference architecture patterns for Guidewire InsuranceSuite Cloud deployments, including integration patterns, data flows, and scalability considerations.

## Prerequisites

- Understanding of enterprise architecture concepts
- Familiarity with Guidewire InsuranceSuite components
- Knowledge of cloud architecture patterns

## Instructions

### Step 1: Understand the Architecture Layers

The system consists of five layers: Digital Experience (Jutro portals), API Gateway (auth and rate limiting), Guidewire Cloud Platform (PC, CC, BC, Contact Manager), Integration Layer (REST, Kafka, batch), and Enterprise Integration (CRM, ERP, rating engines).

### Step 2: Choose Integration Patterns

- **Synchronous API**: Real-time quoting, address validation, credit scoring
- **Asynchronous Event-Driven**: Policy notifications, claims updates via Kafka
- **Batch**: Nightly updates, bulk imports, regulatory reporting via SFTP

### Step 3: Design Data Flows

Map policy lifecycle (submission -> underwriting -> binding -> documents -> distribution) and claims lifecycle (FNOL -> investigation -> settlement -> reporting) through system components.

### Step 4: Implement Security Layers

Stack WAF/DDoS, API Gateway (OAuth2/JWT), Guidewire Hub (MFA, RBAC), AES-256 encryption, PII masking, and TDE for database encryption.

### Step 5: Configure Scalability

Set auto-scaling (2-10 instances, 70% CPU target), L1/L2 caching (in-memory + Redis), connection pooling (10-50), and multi-region deployment for DR.

For full architecture diagrams, data flow specifications, and configuration details, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Environment Strategy

| Environment | Purpose | Data | Integrations |
|-------------|---------|------|--------------|
| Development | Feature development | Synthetic | Mocked |
| Test/QA | Integration testing | Anonymized | Sandbox endpoints |
| UAT | User acceptance | Anonymized | Sandbox endpoints |
| Staging | Pre-production | Prod subset | Production endpoints |
| Production | Live system | Production | Production endpoints |

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Jutro Digital Platform | React-based portals |
| API Gateway | Guidewire Hub | Auth, routing |
| Core Apps | InsuranceSuite | PC, CC, BC |
| Messaging | Apache Kafka | Event streaming |
| Database | PostgreSQL/Oracle | Relational data |
| Cache | Redis | Session, API cache |

## Output

- Architecture diagrams for all layers
- Integration pattern selection guidance
- Data flow specifications
- Security and scalability configurations

## Resources

- [Guidewire Cloud Architecture](https://docs.guidewire.com/cloud/)
- [Integration Framework](https://www.guidewire.com/developers/developer-tools-and-guides/integration-framework)
- [Security Documentation](https://docs.guidewire.com/security/)

## Next Steps

For multi-environment setup, see `guidewire-multi-env-setup`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with deployment |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply guidewire reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire reference architecture for production environments with multiple constraints and team-specific requirements.