---
name: documenso-data-handling
description: |
  Handle document data, signatures, and PII in Documenso integrations.
  Use when managing document lifecycle, handling signed PDFs,
  or implementing data retention policies.
  Trigger with phrases like "documenso data", "signed document",
  "document retention", "documenso PII", "download signed pdf".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Data Handling

## Overview
Best practices for handling documents, signatures, and personally identifiable information (PII) in Documenso integrations.

## Prerequisites
- Understanding of data protection regulations (GDPR, CCPA)
- Secure storage infrastructure
- Encryption capabilities

## Instructions

### Step 1: Document Lifecycle
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
### Step 2: Downloading Signed Documents
import { getDocumensoClient } from "./documenso/client";
### Step 3: PII Handling
interface RecipientPII {
### Step 4: Data Retention
interface RetentionPolicy {
### Step 5: GDPR Compliance
interface DSARResponse {
### Step 6: Encryption at Rest
import crypto from "crypto";

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Document Lifecycle
- Downloading Signed Documents
- PII Handling
- Data Retention
- GDPR Compliance
- Encryption at Rest

## Error Handling
| Data Issue | Cause | Solution |
|------------|-------|----------|
| Download failed | Document not complete | Check status first |
| Storage failed | Permissions | Check bucket policy |
| Decryption failed | Wrong key | Verify encryption key |
| DSAR incomplete | Pagination | Handle all pages |

## Resources
- [GDPR Requirements](https://gdpr.eu/)
- [Document Retention Laws](https://www.nist.gov/publications)
- [AWS S3 Encryption](https://docs.aws.amazon.com/AmazonS3/latest/userguide/serv-side-encryption.html)

## Next Steps
For enterprise RBAC, see `documenso-enterprise-rbac`.

## Examples

**Basic usage**: Apply documenso data handling to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso data handling for production environments with multiple constraints and team-specific requirements.