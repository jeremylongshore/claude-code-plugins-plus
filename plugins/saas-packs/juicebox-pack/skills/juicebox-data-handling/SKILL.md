---
name: juicebox-data-handling
description: |
  Implement Juicebox data privacy and handling.
  Use when managing personal data, implementing GDPR compliance,
  or handling sensitive candidate information.
  Trigger with phrases like "juicebox data privacy", "juicebox GDPR",
  "juicebox PII handling", "juicebox data compliance".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Juicebox Data Handling

## Overview
Implement compliant data handling practices for personal and candidate data from Juicebox.

## Prerequisites
- Understanding of applicable privacy regulations (GDPR, CCPA)
- Data classification framework
- Legal/compliance team sign-off

## Instructions
- Step 1: Data Classification System
- Step 2: PII Handling
- Step 3: Retention Policies
- Step 4: Data Subject Rights
- Step 5: Access Logging

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Data classification system
- PII handling utilities
- Retention policy enforcement
- Data subject rights handlers

## Resources
- [Juicebox Privacy Policy](https://juicebox.ai/privacy)
- [GDPR Guidelines](https://gdpr.eu)

## Next Steps
After data handling, see `juicebox-enterprise-rbac` for access controls.
