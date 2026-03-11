---
name: documenso-core-workflow-b
description: |
  Implement Documenso template-based workflows and direct signing links.
  Use when creating reusable templates, generating documents from templates,
  or implementing direct signing experiences.
  Trigger with phrases like "documenso template", "signing link",
  "direct template", "reusable document", "template workflow".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Documenso Core Workflow B: Templates & Direct Signing

## Overview
Create reusable templates, generate documents from templates, and implement direct signing experiences with Documenso.

## Prerequisites
- Completed `documenso-core-workflow-a`
- Understanding of template-based document generation
- PDF template files ready

## Instructions

### Step 1: Instructions
import { Documenso } from "@documenso/sdk-typescript";
### Step 2: Template Workflow Patterns
// 1. Create template once

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Instructions
- Template Workflow Patterns

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Template not found | Invalid ID or deleted | Verify template exists |
| Recipient mismatch | Wrong number of recipients | Match template roles |
| Field not found | Invalid field ID for prefill | Get field IDs from template |
| Direct link disabled | Feature not enabled | Enable in template settings |
| Duplicate failed | Template in use | Try with different title |

## Resources
- [Templates API](https://github.com/documenso/sdk-typescript/blob/main/docs/sdks/templates/README.md)
- [Embedding Documentation](https://docs.documenso.com/developers/embedding)
- [Direct Templates](https://docs.documenso.com/users/templates)

## Next Steps
For error handling patterns, see `documenso-common-errors`.

## Examples

**Basic usage**: Apply documenso core workflow b to a standard project setup with default configuration options.

**Advanced scenario**: Customize documenso core workflow b for production environments with multiple constraints and team-specific requirements.