---
name: documenso-core-workflow-a
description: |
  Implement Documenso document creation and recipient management workflows.
  Use when creating documents, managing recipients, adding signature fields,
  or building signing workflows with Documenso.
  Trigger with phrases like "documenso document", "create document",
  "add recipient", "documenso signer", "signature field".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Documenso Core Workflow A: Document Creation & Recipients

## Overview
Complete workflow for creating documents, managing recipients, and configuring signature fields in Documenso.

## Prerequisites
- Completed `documenso-install-auth` setup
- Understanding of `documenso-sdk-patterns`
- PDF file ready for signing

## Instructions

### Step 1: Instructions
import { Documenso } from "@documenso/sdk-typescript";
### Step 2: Recipient Roles
Implement recipient roles.
### Step 3: Field Positioning Tips
Implement field positioning tips.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Instructions
- Recipient Roles
- Field Positioning Tips

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Document not found | Invalid ID | Verify document exists |
| Recipient exists | Duplicate email | Update existing recipient |
| Invalid field position | Off-page coordinates | Check page dimensions |
| Cannot modify sent doc | Document already sent | Create new version |
| File too large | PDF exceeds limit | Compress or split PDF |

## Resources
- [Documents API](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documents/README.md)
- [Recipients API](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documentsrecipients/README.md)
- [Fields API](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/documentsfields/README.md)

## Next Steps
For template-based workflows, see `documenso-core-workflow-b`.
