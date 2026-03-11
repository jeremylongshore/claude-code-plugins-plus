---
name: langchain-data-handling
description: |
  Implement LangChain data privacy and handling best practices.
  Use when handling sensitive data, implementing PII protection,
  or ensuring data compliance in LLM applications.
  Trigger with phrases like "langchain data privacy", "langchain PII",
  "langchain GDPR", "langchain data handling", "langchain compliance".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Data Handling

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Best practices for handling sensitive data, PII protection, and compliance in LangChain applications including detection, masking, retention, consent, and audit logging.

## Prerequisites
- Understanding of data privacy regulations (GDPR, CCPA)
- LangChain application processing user data
- Data classification framework

## Instructions

### Step 1: Detect and Mask PII
Build a `PIIDetector` class with regex patterns for email, phone, SSN, credit card, IP address, and date of birth. Implement `detect()`, `mask()`, and `redact()` methods.

### Step 2: Build Privacy Pipeline
Wrap chains with PII protection using `RunnableLambda` preprocessing that redacts PII before sending to the LLM.

### Step 3: Enforce Data Retention
Implement `DataRetentionManager` with configurable retention periods, auto-cleanup of expired interactions, and GDPR right-to-erasure support.

### Step 4: Manage Consent
Build `ConsentManager` with consent types (LLM processing, retention, analytics, training) and decorator-based consent enforcement.

### Step 5: Enable Audit Logging
Create `AuditLogger` and `AuditCallback` to log all LLM calls with user ID, model, token count, and PII detection status.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete PII detector, privacy pipeline, and compliance code.

## Output
- PII detection and masking
- Privacy-wrapped chain pipeline
- Data retention management
- Consent management system
- Audit logging

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| PII not detected | Missing pattern | Add regex to PIIPattern list |
| Retention not enforced | Cleanup not scheduled | Add cron job for cleanup |
| Consent check failed | User not registered | Create consent record first |

## Examples


**Basic usage**: Apply langchain data handling to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain data handling for production environments with multiple constraints and team-specific requirements.

## Resources
- [GDPR Overview](https://gdpr.eu/)
- [CCPA Compliance](https://oag.ca.gov/privacy/ccpa)
- [OpenAI Data Usage Policy](https://openai.com/policies/api-data-usage-policies)

## Next Steps
Use `langchain-security-basics` for additional security measures.