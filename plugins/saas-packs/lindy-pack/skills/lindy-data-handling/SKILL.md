---
name: lindy-data-handling
description: |
  Best practices for handling data with Lindy AI.
  Use when managing sensitive data, implementing data privacy,
  or ensuring data compliance.
  Trigger with phrases like "lindy data", "lindy privacy",
  "lindy PII", "lindy data handling", "lindy GDPR".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Lindy Data Handling

## Overview
Best practices for secure and compliant data handling with Lindy AI.

## Prerequisites
- Understanding of data privacy requirements
- Knowledge of applicable regulations (GDPR, CCPA, HIPAA)
- Access to data classification documentation

## Instructions

### Step 1: Data Classification
### Step 2: PII Detection and Redaction
### Step 3: Secure Data Pipeline
### Step 4: Data Retention Management
### Step 5: GDPR Compliance

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Data Handling Checklist
## Output
- Data classification system
- PII detection and redaction
- Secure data pipeline
- Retention management
- GDPR compliance handlers

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| PII leaked | Missing redaction | Enable auto-redaction |
| Retention exceeded | No cleanup | Schedule retention job |
| Classification missing | No policy | Default to restricted |

## Resources
- [Lindy Privacy Policy](https://lindy.ai/privacy)
- [Lindy Security](https://lindy.ai/security)
- [GDPR Guidelines](https://gdpr.eu/)

## Next Steps
Proceed to `lindy-enterprise-rbac` for access control.
