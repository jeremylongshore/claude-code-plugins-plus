---
name: openevidence-reference-architecture
description: |
  Implement OpenEvidence reference architecture with best-practice project layout.
  Use when designing new clinical AI integrations, reviewing project structure,
  or establishing architecture standards for healthcare applications.
  Trigger with phrases like "openevidence architecture", "openevidence best practices",
  "openevidence project structure", "clinical ai architecture".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence Reference Architecture

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Production-ready layered architecture for OpenEvidence clinical AI integrations. Covers project structure, client wrapper with caching/monitoring, service facade with PHI handling, EHR integration (FHIR/CDS Hooks), and configuration management.

## Prerequisites
- Understanding of layered architecture
- OpenEvidence SDK knowledge
- Healthcare compliance requirements (HIPAA)
- TypeScript/Node.js project setup

## Layer Architecture
```
API Layer          -> Controllers, Routes, Webhooks, Middleware
Service Layer      -> Business Logic, Orchestration, Validation
OpenEvidence Layer -> Client, Types, Caching, Error Handling
Compliance Layer   -> HIPAA Audit, PHI Handling, Encryption
Integration Layer  -> EHR/FHIR, Notifications, External Services
Infrastructure     -> Database, Cache, Queue, Monitoring
```

## Instructions

### Step 1: Set Up Project Structure
Organize into `src/openevidence/` (client, config, types, errors, cache), `src/services/clinical/` (query, deepconsult, drug-info), `src/api/` (routes, middleware), `src/compliance/` (HIPAA audit, PHI, encryption), and `src/integrations/` (EHR, notifications).

### Step 2: Build Client Wrapper
Create `OpenEvidenceService` with caching, metrics collection, HIPAA audit logging, and health check. Use singleton pattern with cache-first strategy.

### Step 3: Create Service Facade
Build `ClinicalEvidenceService` that sanitizes PHI before queries, formats responses for clinical use, and handles drug interaction checks.

### Step 4: Implement EHR Integration
Add FHIR CDS Hooks endpoints for `patient-view` and `medication-prescribe` hooks. Extract conditions and medications from FHIR prefetch data.

### Step 5: Configure Management
Use convict for typed configuration with environment-specific JSON files. Mark sensitive fields (apiKey) and validate strictly.

## Output
- Layered architecture with separation of concerns
- Client wrapper with caching, metrics, and audit logging
- Service facade with PHI sanitization
- EHR integration (FHIR CDS Hooks)
- Typed configuration management (convict)

## Error Handling
| Architecture Issue | Detection | Resolution |
|--------------------|-----------|------------|
| Layer violation | Code review | Enforce import boundaries |
| PHI leak | Audit log review | Add PHI detection middleware |
| Cache stale data | Clinical complaint | Review TTL strategy |
| EHR integration fails | CDS Hook errors | Check FHIR endpoint config |

## Examples

### Data Flow
```
User -> API Gateway -> PHI Sanitizer -> Cache Check -> OpenEvidence API -> Cache Store -> Response
                          |                                                      |
                     HIPAA Audit Log                                       Audit Log
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [HL7 FHIR](https://www.hl7.org/fhir/)
- [CDS Hooks](https://cds-hooks.hl7.org/)
- [SMART on FHIR](https://smarthealthit.org/)